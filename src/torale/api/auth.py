from typing import Annotated

from fastapi import Depends

from torale.api.users import User, current_active_user

# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(current_active_user)]
