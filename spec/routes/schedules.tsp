namespace Calendar;

using Http;
using OpenAPI;

@route("/schedules")
@tag("Schedules")
@useAuth(BearerAuth)
interface Schedules {
  @summary("Create availability schedule")
  @operationId("Schedules_create")
  @post
  create(@body body: CreateScheduleRequest): Created<Schedule> | ValidationError | UnauthorizedError | ConflictError;

  @summary("List current user's schedules")
  @operationId("Schedules_list")
  @get
  list(): Ok<ApiList<Schedule>> | UnauthorizedError;

  @summary("Get default schedule")
  @operationId("Schedules_getDefault")
  @get
  @route("default")
  getDefault(): Ok<Schedule> | UnauthorizedError | NotFoundError;

  @summary("Get schedule by id")
  @operationId("Schedules_get")
  @get
  @route("{scheduleId}")
  get(@path scheduleId: Uuid): Ok<Schedule> | UnauthorizedError | ForbiddenError | NotFoundError;

  @summary("Update schedule by id")
  @operationId("Schedules_update")
  @patch
  @route("{scheduleId}")
  update(@path scheduleId: Uuid, @body body: UpdateScheduleRequest):
    Ok<Schedule> | ValidationError | UnauthorizedError | ForbiddenError | NotFoundError | ConflictError;

  @summary("Delete schedule by id")
  @operationId("Schedules_delete")
  @delete
  @route("{scheduleId}")
  delete(@path scheduleId: Uuid): NoContent | UnauthorizedError | ForbiddenError | NotFoundError | ConflictError;
}
