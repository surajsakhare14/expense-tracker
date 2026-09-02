"""Business logic for system and user-owned categories."""

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryDataResponse,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdateRequest,
)


class CategoryService:
    """Category validation, lifecycle, and ownership rules."""

    def __init__(self, session: Session):
        self.repository = CategoryRepository(session)

    def create_category(self, user_id: str, request: CategoryCreateRequest) -> CategoryDataResponse:
        if self.repository.has_active_name(
            user_id, request.name, request.type
        ) or self.repository.has_active_system_name(request.name, request.type):
            raise AppException(
                code="CATEGORY_NAME_ALREADY_EXISTS",
                message="An active category with this name and type already exists.",
                status_code=409,
            )
        category = self.repository.create_category(user_id, request.name, request.type)
        return CategoryDataResponse(data=self._to_response(category))

    def list_categories(
        self, user_id: str, category_type: str | None = None
    ) -> CategoryListResponse:
        categories = self.repository.list_categories(user_id, category_type)
        return CategoryListResponse(data=[self._to_response(category) for category in categories])

    def get_category(self, category_id: str, user_id: str) -> CategoryDataResponse:
        category = self.repository.get_visible_category(category_id, user_id)
        if not category:
            raise self._not_found()
        return CategoryDataResponse(data=self._to_response(category))

    def update_category(
        self, category_id: str, user_id: str, request: CategoryUpdateRequest
    ) -> CategoryDataResponse:
        category = self.repository.get_visible_category(category_id, user_id)
        if not category:
            raise self._not_found()
        if category.is_system:
            raise self._system_immutable()

        values = request.model_dump(exclude_unset=True)
        new_type = values.get("type", category.category_type)
        if (
            new_type != category.category_type
            and self.repository.has_transaction_references(category.id)
        ):
            raise AppException(
                code="CATEGORY_TYPE_IMMUTABLE_AFTER_USE",
                message=(
                    "A category type cannot be changed after it has been used by a transaction."
                ),
                status_code=409,
            )
        if "name" in values and self.repository.has_active_name(
            user_id, values["name"], new_type, category.id
        ):
            raise AppException(
                code="CATEGORY_NAME_ALREADY_EXISTS",
                message="An active category with this name and type already exists.",
                status_code=409,
            )
        category = self.repository.update_category(category, values)
        return CategoryDataResponse(data=self._to_response(category))

    def archive_category(self, category_id: str, user_id: str) -> None:
        category = self.repository.get_visible_category(category_id, user_id)
        if not category:
            raise self._not_found()
        if category.is_system:
            raise self._system_immutable()
        self.repository.archive_category(category)

    @staticmethod
    def _to_response(category: Category) -> CategoryResponse:
        return CategoryResponse.model_validate(category)

    @staticmethod
    def _not_found() -> AppException:
        return AppException(
            code="CATEGORY_NOT_FOUND", message="Category could not be found.", status_code=404
        )

    @staticmethod
    def _system_immutable() -> AppException:
        return AppException(
            code="SYSTEM_CATEGORY_IMMUTABLE",
            message="System categories cannot be modified or archived.",
            status_code=409,
        )
