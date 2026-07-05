namespace Calendar;

using Http;
using OpenAPI;

@route("/bookings")
@tag("Bookings")
interface Bookings {
  @summary("Create booking from event type or share link")
  @operationId("Bookings_create")
  @post
  create(@body body: CreateBookingRequest):
    Created<Booking> | ValidationError | NotFoundError | GoneError | ConflictError | TooManyRequestsError;

  @summary("List current user's bookings")
  @operationId("Bookings_list")
  @get
  @useAuth(BearerAuth)
  list(@query status?: BookingStatus, @query from?: LocalDate, @query to?: LocalDate):
    Ok<ApiList<Booking>> | ValidationError | UnauthorizedError;

  @summary("Get booking by uid")
  @operationId("Bookings_get")
  @get
  @route("{bookingUid}")
  @useAuth(BearerAuth)
  get(@path bookingUid: string): Ok<Booking> | UnauthorizedError | ForbiddenError | NotFoundError;

  @summary("Confirm booking as event owner")
  @operationId("Bookings_confirm")
  @post
  @route("{bookingUid}/confirm")
  @useAuth(BearerAuth)
  confirm(@path bookingUid: string): Ok<Booking> | UnauthorizedError | ForbiddenError | NotFoundError | ConflictError;

  @summary("Decline booking as event owner")
  @operationId("Bookings_decline")
  @post
  @route("{bookingUid}/decline")
  @useAuth(BearerAuth)
  decline(@path bookingUid: string, @body body: BookingActionRequest):
    Ok<Booking> | ValidationError | UnauthorizedError | ForbiddenError | NotFoundError | ConflictError;

  @summary("Cancel booking as event owner")
  @operationId("Bookings_cancel")
  @post
  @route("{bookingUid}/cancel")
  @useAuth(BearerAuth)
  cancel(@path bookingUid: string, @body body: BookingActionRequest):
    Ok<Booking> | ValidationError | UnauthorizedError | ForbiddenError | NotFoundError | ConflictError;
}

@route("/public/bookings")
@tag("Public Bookings")
interface PublicBookings {
  @summary("Confirm booking as attendee")
  @operationId("PublicBookings_confirmAttendee")
  @post
  @route("{bookingUid}/confirm")
  confirmAttendee(@path bookingUid: string, @query token: PublicToken):
    Ok<Booking> | ValidationError | NotFoundError | GoneError | ConflictError;
}
