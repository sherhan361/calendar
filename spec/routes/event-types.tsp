namespace Calendar;

using Http;
using OpenAPI;

@route("/event-types")
@tag("Event Types")
@useAuth(BearerAuth)
interface EventTypes {
  @summary("Create event type")
  @operationId("EventTypes_create")
  @post
  create(@body body: CreateEventTypeRequest): Created<EventType> | ValidationError | UnauthorizedError | NotFoundError | ConflictError;

  @summary("List current user's event types")
  @operationId("EventTypes_list")
  @get
  list(@query includeHidden?: boolean): Ok<ApiList<EventType>> | UnauthorizedError;

  @summary("Get event type by id")
  @operationId("EventTypes_get")
  @get
  @route("{eventTypeId}")
  get(@path eventTypeId: Uuid): Ok<EventType> | UnauthorizedError | ForbiddenError | NotFoundError;

  @summary("Update event type by id")
  @operationId("EventTypes_update")
  @patch
  @route("{eventTypeId}")
  update(@path eventTypeId: Uuid, @body body: UpdateEventTypeRequest):
    Ok<EventType> | ValidationError | UnauthorizedError | ForbiddenError | NotFoundError | ConflictError;

  @summary("Delete event type by id")
  @operationId("EventTypes_delete")
  @delete
  @route("{eventTypeId}")
  delete(@path eventTypeId: Uuid): NoContent | UnauthorizedError | ForbiddenError | NotFoundError | ConflictError;
}

@route("/public/users/{username}/event-types")
@tag("Public Event Types")
interface PublicEventTypes {
  @summary("Get public event type by owner username and slug")
  @operationId("PublicEventTypes_get")
  @get
  @route("{slug}")
  get(@path username: Username, @path slug: Slug, @query shareToken?: PublicToken):
    Ok<PublicEventType> | NotFoundError | GoneError;
}

@route("/public/users")
@tag("Public Event Types")
interface PublicUsers {
  @summary("Get public user profile with visible event types")
  @operationId("PublicUsers_get")
  @get
  @route("{username}")
  get(@path username: Username): Ok<PublicUserPage> | NotFoundError;
}
