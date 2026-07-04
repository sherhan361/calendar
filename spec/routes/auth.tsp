namespace Calendar;

using Http;
using OpenAPI;

@route("/auth")
@tag("Auth")
interface Auth {
  @summary("Register a new user")
  @operationId("Auth_register")
  @post
  @route("register")
  register(@body body: RegisterRequest): Created<AuthSession> | ValidationError | ConflictError;

  @summary("Login with email and password")
  @operationId("Auth_login")
  @post
  @route("login")
  login(@body body: LoginRequest): Ok<AuthSession> | ValidationError | UnauthorizedError;

  @summary("Invalidate current session")
  @operationId("Auth_logout")
  @post
  @route("logout")
  @useAuth(BearerAuth)
  logout(): NoContent | UnauthorizedError;
}
