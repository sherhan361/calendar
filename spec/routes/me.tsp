namespace Calendar;

using Http;
using OpenAPI;

@route("/me")
@tag("Me")
@useAuth(BearerAuth)
interface Me {
  @summary("Get current user profile")
  @operationId("Me_get")
  @get
  getMe(): Ok<User> | UnauthorizedError;

  @summary("Update current user profile")
  @operationId("Me_update")
  @patch
  updateMe(@body body: UpdateMeRequest): Ok<User> | ValidationError | UnauthorizedError | ConflictError;
}
