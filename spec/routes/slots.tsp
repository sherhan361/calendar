namespace Calendar;

using Http;
using OpenAPI;

@route("/slots")
@tag("Slots")
@useAuth(BearerAuth)
interface Slots {
  @summary("Get available slots for owned event type")
  @operationId("Slots_get")
  @get
  get(
    @query eventTypeId: Uuid,
    @query start: LocalDate,
    @query end: LocalDate,
    @query timeZone?: TimeZone,
    @query durationMinutes?: int32,
  ): Ok<SlotsResponse> | ValidationError | UnauthorizedError | ForbiddenError | NotFoundError;
}

@route("/public/slots")
@tag("Public Slots")
interface PublicSlots {
  @summary("Get public available slots for an event type")
  @operationId("PublicSlots_get")
  @get
  get(
    @query username: Username,
    @query eventTypeSlug: Slug,
    @query start: LocalDate,
    @query end: LocalDate,
    @query timeZone?: TimeZone,
    @query durationMinutes?: int32,
    @query shareToken?: PublicToken,
  ): Ok<SlotsResponse> | ValidationError | NotFoundError | GoneError;
}
