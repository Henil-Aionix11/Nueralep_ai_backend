"""Service layer for tenant authentication and management operations."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import csv

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from passlib.context import CryptContext
from openpyxl import load_workbook

from app.core.database import get_db
from app.core.repositories.tenant_repository import TenantRepository
from app.core.repositories.agent_repository import AgentRepository
from app.core.models.tenant_model import Tenant
from app.core.schema.tenant_schema import TenantCreate, TenantUpdate, TenantLogin
from app.core.exceptions.api_exceptions import (
    ApiNotFoundError,
    ApiConflictError,
    ApiInternalServerError,
)
from app.core.utils.file_utils import (
    ensure_directory,
    generate_unique_filename,
    validate_file_extension,
)
from app.web.settings import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TenantService:
    """Handles business logic for tenant operations."""
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize tenant service.

        Args:
            session: Database session
        """
        self.tenant_repo = TenantRepository(session)
        self.agent_repo = AgentRepository(session)
        self.session = session
        self.dataset_base_dir = Path(settings.dataset_upload_dir).resolve()

    # ==================== PASSWORD UTILITIES ====================

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    # ==================== TENANT AUTHENTICATION ====================

    async def authenticate_tenant(self, email: str, password: str) -> Tenant:
        """Authenticate tenant by email and password.

        Args:
            email: Tenant email
            password: Tenant password

        Returns:
            Authenticated tenant

        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Get tenant by email
            tenant = await self.tenant_repo.get_by_field("email", email.lower())

            if not tenant:
                logger.warning(f"Login attempt with non-existent email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                )

            # Check if tenant is active
            if not tenant.is_active or tenant.is_deleted:
                logger.warning(f"Login attempt for inactive tenant: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tenant account is inactive",
                )

            # Verify password
            if not self.verify_password(password, tenant.hashed_password):
                logger.warning(f"Failed login attempt for tenant: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                )

            logger.info(f"Tenant authenticated successfully: {email}")
            return tenant

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            raise ApiInternalServerError(
                error=f"Authentication failed: {str(e)}",
                message="Authentication failed",
            ) from e

    # ==================== TENANT RETRIEVAL ====================

    async def get_tenant_by_id(self, tenant_id: int) -> Tenant:
        """Get tenant by ID with agents.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant object with agents

        Raises:
            ApiNotFoundError: If tenant not found
        """
        try:
            tenant = await self.tenant_repo.get_by_id(tenant_id)

            if not tenant or tenant.is_deleted:
                logger.warning(f"Tenant not found: {tenant_id}")
                raise ApiNotFoundError(
                    error=f"Tenant with ID {tenant_id} not found",
                    message=f"Tenant with ID {tenant_id} not found",
                )

            return tenant

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get tenant by ID {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve tenant: {str(e)}",
                message="Failed to retrieve tenant",
            ) from e

    async def get_tenant_by_email(self, email: str) -> Optional[Tenant]:
        """Get tenant by email.

        Args:
            email: Tenant email

        Returns:
            Tenant object or None
        """
        try:
            tenant = await self.tenant_repo.get_by_field("email", email.lower())
            return tenant
        except Exception as e:
            logger.error(f"Failed to get tenant by email {email}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve tenant: {str(e)}",
                message="Failed to retrieve tenant",
            ) from e

    async def get_all_tenants(self) -> list[Tenant]:
        """Get all active tenants.

        Returns:
            List of active tenants
        """
        try:
            tenants = await self.tenant_repo.get_all_by_filter(is_deleted=False)
            logger.debug(f"Retrieved {len(tenants)} active tenants")
            return tenants

        except Exception as e:
            logger.error(f"Failed to get all tenants: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve tenants: {str(e)}",
                message="Failed to retrieve tenants",
            ) from e


    # In TenantAuthService
    async def get_tenant_agents(self, tenant_id: int):
        tenant = await self.get_tenant_by_id(tenant_id)
        return tenant.agents if tenant else []
    
    # ==================== DATASET MANAGEMENT ====================

    async def upload_dataset(
        self, tenant_id: int, upload_file: UploadFile
    ) -> Dict[str, Any]:
        """Upload or replace tenant dataset."""
        tenant = await self.get_tenant_by_id(tenant_id)

        if not upload_file or not upload_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File is required"
            )

        is_valid, error_message = validate_file_extension(
            upload_file.filename, settings.dataset_allowed_extensions
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_message
            )

        file_bytes = await upload_file.read()
        await upload_file.close()

        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty files are not allowed",
            )

        previous_path = tenant.dataset_storage_path

        tenant_dir = Path(
            ensure_directory(str(self.dataset_base_dir / f"tenant_{tenant_id}"))
        )
        unique_filename = generate_unique_filename(
            upload_file.filename, prefix=f"tenant{tenant_id}"
        )
        new_file_path = tenant_dir / unique_filename

        with open(new_file_path, "wb") as destination:
            destination.write(file_bytes)

        extension = Path(upload_file.filename).suffix.lower()

        preview = self._build_dataset_preview(new_file_path, extension)

        metadata = {
            "original_name": upload_file.filename,
            "size_bytes": len(file_bytes),
            "uploaded_at": datetime.utcnow().isoformat(),
            "extension": extension,
            "preview": preview,
        }

        updated_tenant = await self.tenant_repo.update(
            record_id=tenant_id,
            update_data={
                "dataset_storage_path": str(new_file_path),
                "dataset_metadata": metadata,
            },
            commit=True,
        )

        self._cleanup_previous_dataset_file(previous_path, new_file_path)

        logger.info(f"Dataset uploaded for tenant {tenant_id}")

        return {
            "storage_path": updated_tenant.dataset_storage_path,
            "metadata": updated_tenant.dataset_metadata,
        }

    async def get_dataset_preview(self, tenant_id: int) -> Dict[str, Any]:
        """Return stored dataset metadata for preview."""
        tenant = await self.get_tenant_by_id(tenant_id)

        if not tenant.dataset_storage_path or not tenant.dataset_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No dataset uploaded for this tenant",
            )

        return {
            "storage_path": tenant.dataset_storage_path,
            "metadata": tenant.dataset_metadata,
        }

    def _build_dataset_preview(
        self, file_path: Path, extension: str
    ) -> Dict[str, Any]:
        """Return preview data for supported file types."""
        try:
            if extension == ".csv":
                return self._preview_csv(file_path)
            if extension == ".xlsx":
                return self._preview_excel(file_path)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type for preview",
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Failed to build dataset preview: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to read dataset. Please upload a valid CSV or Excel file.",
            ) from exc

    def _preview_csv(self, file_path: Path) -> Dict[str, Any]:
        columns: list[str] = []
        rows: list[Dict[str, Any]] = []

        with open(
            file_path, mode="r", encoding="utf-8", errors="ignore", newline=""
        ) as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader, None)

            if header is None:
                return {"columns": [], "rows": []}

            columns = self._normalize_header(list(header))

            for row in reader:
                rows.append(self._row_to_dict(columns, row))
                if len(rows) >= settings.dataset_preview_limit:
                    break

        return {"columns": columns, "rows": rows}

    def _preview_excel(self, file_path: Path) -> Dict[str, Any]:
        rows: list[Dict[str, Any]] = []
        workbook = load_workbook(filename=file_path, read_only=True, data_only=True)

        try:
            sheet = workbook.active
            rows_iter = sheet.iter_rows(values_only=True)
            header = next(rows_iter, None)

            if header is None:
                return {"columns": [], "rows": []}

            columns = self._normalize_header(list(header))

            for row in rows_iter:
                row_values = list(row) if row is not None else []
                rows.append(self._row_to_dict(columns, row_values))
                if len(rows) >=settings.dataset_preview_limit:
                    break

            return {"columns": columns, "rows": rows}
        finally:
            workbook.close()

    def _normalize_header(self, header_values: list[Any]) -> list[str]:
        columns: list[str] = []
        for idx, value in enumerate(header_values):
            column_name = ""
            if value is not None:
                column_name = str(value).strip()
            if not column_name:
                column_name = f"Column {idx + 1}"
            columns.append(column_name)
        return columns

    def _row_to_dict(
        self, columns: list[str], row_values: list[Any]
    ) -> Dict[str, Any]:
        row_data: Dict[str, Any] = {}
        for idx, column in enumerate(columns):
            cell_value = ""
            if row_values and idx < len(row_values):
                value = row_values[idx]
                cell_value = "" if value is None else str(value)
            row_data[column] = cell_value
        return row_data

    def _cleanup_previous_dataset_file(
        self, previous_path: Optional[str], new_path: Path
    ) -> None:
        if not previous_path or previous_path == str(new_path):
            return

        try:
            previous = Path(previous_path)
            if previous.exists():
                previous.unlink()
                logger.debug(f"Removed previous dataset file: {previous_path}")
        except Exception as exc:
            logger.warning(
                f"Failed to delete previous dataset file {previous_path}: {exc}"
            )

    # ==================== TENANT UPDATE ====================

    async def update_tenant(self, tenant_id: int, update_data: TenantUpdate) -> Tenant:
        """Update tenant information.

        Args:
            tenant_id: Tenant ID
            update_data: Data to update

        Returns:
            Updated tenant object

        Raises:
            ApiNotFoundError: If tenant not found
            ApiInternalServerError: If update fails
        """
        try:
            # Check if tenant exists
            tenant = await self.get_tenant_by_id(tenant_id)

            # Update tenant
            updated_tenant = await self.tenant_repo.update(
                record_id=tenant_id, update_data=update_data, commit=True
            )

            logger.info(f"Updated tenant: {tenant_id}")
            return updated_tenant

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to update tenant: {str(e)}",
                message="Failed to update tenant",
            ) from e

    # ==================== TENANT SOFT DELETE ====================

    async def soft_delete_tenant(self, tenant_id: int) -> bool:
        """Soft delete tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            True if successful

        Raises:
            ApiNotFoundError: If tenant not found
        """
        try:
            tenant = await self.get_tenant_by_id(tenant_id)

            # Soft delete
            await self.tenant_repo.update(
                tenant_id, {"is_deleted": True}, commit=True
            )

            logger.info(f"Soft deleted tenant: {tenant_id}")
            return True

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to delete tenant: {str(e)}",
                message="Failed to delete tenant",
            ) from e
            



# Dependency injection
async def get_tenant_service(
    session: AsyncSession = Depends(get_db),
) -> TenantService:  # type: ignore
    """Get tenant service instance.

    Args:
        session: Database session

    Yields:
        TenantService instance
    """
    yield TenantService(session)
