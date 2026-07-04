namespace Calendar;

using Http;
using OpenAPI;

@route("/event-types/{eventTypeId}/share-links")
@tag("Share Links")
@useAuth(BearerAuth)
interface ShareLinks {
  @summary("Create share link for an event type")
  @operationId("ShareLinks_create")
  @post
  create(@path eventTypeId: Uuid, @body body: CreateShareLinkRequest):
    Created<ShareLink> | ValidationError | UnauthorizedError | ForbiddenError | NotFoundError;

  @summary("List share links for an event type")
  @operationId("ShareLinks_list")
  @get
  list(@path eventTypeId: Uuid): Ok<ApiList<ShareLink>> | UnauthorizedError | ForbiddenError | NotFoundError;

  @summary("Delete share link")
  @operationId("ShareLinks_delete")
  @delete
  @route("{shareLinkId}")
  delete(@path eventTypeId: Uuid, @path shareLinkId: Uuid): NoContent | UnauthorizedError | ForbiddenError | NotFoundError;
}

@route("/public/share-links")
@tag("Public Share Links")
interface PublicShareLinks {
  @summary("Resolve public share link")
  @operationId("PublicShareLinks_get")
  @get
  @route("{token}")
  get(@path token: PublicToken): Ok<PublicShareLink> | NotFoundError | GoneError;
}
