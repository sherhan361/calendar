namespace Calendar;

using Http;

@format("uuid")
scalar Uuid extends string;

@format("email")
scalar Email extends string;

@format("date")
scalar LocalDate extends string;

@pattern("^([01]\\d|2[0-3]):[0-5]\\d$")
scalar LocalTime extends string;

@pattern("^[a-z0-9]+(?:-[a-z0-9]+)*$")
scalar Slug extends string;

@pattern("^[A-Za-z0-9_-]{16,128}$")
scalar PublicToken extends string;

@pattern("^[A-Za-z0-9_-]{8,128}$")
scalar IdempotencyKey extends string;

@pattern("^[A-Za-z][A-Za-z0-9_-]{2,31}$")
scalar Username extends string;

alias TimeZone = string;

model ApiSuccess<T> {
  status: "success";
  data: T;
}

model ApiList<T> {
  items: T[];
}

model Ok<T> {
  @statusCode statusCode: 200;
  @body body: ApiSuccess<T>;
}

model Created<T> {
  @statusCode statusCode: 201;
  @body body: ApiSuccess<T>;
}

model NoContent {
  @statusCode statusCode: 204;
}

model ErrorDetail {
  field?: string;
  message: string;
}

model ApiError<Code extends string> {
  status: "error";
  error: {
    code: Code;
    message: string;
    details?: ErrorDetail[];
  };
}

@error
model ValidationError {
  @statusCode statusCode: 400;
  @body body: ApiError<"validation_error">;
}

@error
model UnauthorizedError {
  @statusCode statusCode: 401;
  @body body: ApiError<"unauthorized">;
}

@error
model ForbiddenError {
  @statusCode statusCode: 403;
  @body body: ApiError<"forbidden">;
}

@error
model NotFoundError {
  @statusCode statusCode: 404;
  @body body: ApiError<"not_found">;
}

@error
model ConflictError {
  @statusCode statusCode: 409;
  @body body: ApiError<"conflict">;
}

@error
model GoneError {
  @statusCode statusCode: 410;
  @body body: ApiError<"link_expired">;
}
