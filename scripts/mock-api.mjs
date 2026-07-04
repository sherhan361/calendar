#!/usr/bin/env node

import { PrismaClient } from "@prisma/client";
import { createServer } from "node:http";
import { randomUUID } from "node:crypto";

const prisma = new PrismaClient();
const port = Number(process.env.API_PORT || process.env.PORT || 8000);
const host = process.env.API_HOST || "127.0.0.1";
const weekdayByIndex = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];

const server = createServer(async (request, response) => {
  try {
    setCors(response);

    if (request.method === "OPTIONS") {
      response.writeHead(204);
      response.end();
      return;
    }

    const url = new URL(request.url ?? "/", `http://${request.headers.host ?? `${host}:${port}`}`);
    const method = request.method ?? "GET";
    const pathname = trimTrailingSlash(url.pathname);

    if (method === "GET" && pathname === "/healthz") return send(response, 200, { status: "ok" });
    if (method === "POST" && pathname === "/auth/login") return login(request, response);
    if (method === "POST" && pathname === "/auth/register") return register(request, response);
    if (method === "POST" && pathname === "/auth/logout") return sendNoContent(response);

    const publicEventMatch = pathname.match(/^\/public\/users\/([^/]+)\/event-types\/([^/]+)$/);
    if (publicEventMatch && method === "GET") return getPublicEventType(response, publicEventMatch[1], publicEventMatch[2], url.searchParams);

    const publicShareMatch = pathname.match(/^\/public\/share-links\/([^/]+)$/);
    if (publicShareMatch && method === "GET") return getPublicShareLink(response, publicShareMatch[1]);

    if (method === "GET" && pathname === "/public/slots") return getPublicSlots(response, url.searchParams);

    const publicBookingConfirmMatch = pathname.match(/^\/public\/bookings\/([^/]+)\/confirm$/);
    if (publicBookingConfirmMatch && method === "POST") return confirmAttendee(response, publicBookingConfirmMatch[1], url.searchParams);

    const currentUser = await requireUser(request, response);
    if (!currentUser) return;

    if (method === "GET" && pathname === "/me") return sendOk(response, mapUser(currentUser));
    if (method === "PATCH" && pathname === "/me") return updateMe(request, response, currentUser);

    if (pathname === "/schedules") {
      if (method === "GET") return listSchedules(response, currentUser);
      if (method === "POST") return createSchedule(request, response, currentUser);
    }

    if (method === "GET" && pathname === "/schedules/default") return getDefaultSchedule(response, currentUser);

    const scheduleMatch = pathname.match(/^\/schedules\/([^/]+)$/);
    if (scheduleMatch) {
      if (method === "GET") return getSchedule(response, currentUser, scheduleMatch[1]);
      if (method === "PATCH") return updateSchedule(request, response, currentUser, scheduleMatch[1]);
      if (method === "DELETE") return deleteSchedule(response, currentUser, scheduleMatch[1]);
    }

    if (pathname === "/event-types") {
      if (method === "GET") return listEventTypes(response, currentUser, url.searchParams);
      if (method === "POST") return createEventType(request, response, currentUser);
    }

    const shareLinksMatch = pathname.match(/^\/event-types\/([^/]+)\/share-links(?:\/([^/]+))?$/);
    if (shareLinksMatch) {
      if (method === "GET" && !shareLinksMatch[2]) return listShareLinks(response, currentUser, shareLinksMatch[1]);
      if (method === "POST" && !shareLinksMatch[2]) return createShareLink(request, response, currentUser, shareLinksMatch[1]);
      if (method === "DELETE" && shareLinksMatch[2]) return deleteShareLink(response, currentUser, shareLinksMatch[1], shareLinksMatch[2]);
    }

    const eventTypeMatch = pathname.match(/^\/event-types\/([^/]+)$/);
    if (eventTypeMatch) {
      if (method === "GET") return getEventType(response, currentUser, eventTypeMatch[1]);
      if (method === "PATCH") return updateEventType(request, response, currentUser, eventTypeMatch[1]);
      if (method === "DELETE") return deleteEventType(response, currentUser, eventTypeMatch[1]);
    }

    if (method === "GET" && pathname === "/slots") return getOwnedSlots(response, currentUser, url.searchParams);

    if (pathname === "/bookings") {
      if (method === "GET") return listBookings(response, currentUser, url.searchParams);
      if (method === "POST") return createBooking(request, response);
    }

    const bookingActionMatch = pathname.match(/^\/bookings\/([^/]+)(?:\/(confirm|decline|cancel))?$/);
    if (bookingActionMatch) {
      if (method === "GET" && !bookingActionMatch[2]) return getBooking(response, currentUser, bookingActionMatch[1]);
      if (method === "POST" && bookingActionMatch[2] === "confirm") return updateBookingStatus(response, currentUser, bookingActionMatch[1], "confirmed");
      if (method === "POST" && bookingActionMatch[2] === "decline") return updateBookingStatus(response, currentUser, bookingActionMatch[1], "declined", await readJson(request));
      if (method === "POST" && bookingActionMatch[2] === "cancel") return updateBookingStatus(response, currentUser, bookingActionMatch[1], "cancelled", await readJson(request));
    }

    sendError(response, 404, "not_found", "Endpoint not found.");
  } catch (error) {
    console.error(error);
    sendError(response, 500, "internal_error", "Mock API failed.");
  }
});

server.listen(port, host, () => {
  console.log(`Mock API: http://${host}:${port}`);
});

process.on("SIGINT", stop);
process.on("SIGTERM", stop);

async function stop() {
  await prisma.$disconnect();
  server.close(() => process.exit(0));
}

async function login(request, response) {
  const body = await readJson(request);
  const user = await prisma.user.findUnique({ where: { email: body.email ?? "" } });
  if (!user) return sendError(response, 401, "unauthorized", "Unknown email.");

  sendOk(response, {
    accessToken: tokenFor(user.id),
    tokenType: "Bearer",
    user: mapUser(user),
  });
}

async function register(request, response) {
  const body = await readJson(request);
  if (!body.email || !body.username || !body.name) {
    return sendError(response, 400, "validation_error", "email, username and name are required.");
  }

  const existing = await prisma.user.findFirst({
    where: { OR: [{ email: body.email }, { username: body.username }] },
  });
  if (existing) return sendError(response, 409, "conflict", "User already exists.");

  const user = await prisma.user.create({
    data: {
      email: body.email,
      username: body.username,
      name: body.name,
      timeZone: body.timeZone || "Europe/Moscow",
    },
  });

  const schedule = await prisma.schedule.create({
    data: {
      ownerId: user.id,
      name: "Working hours",
      timeZone: user.timeZone,
      isDefault: true,
      availabilityJson: JSON.stringify(defaultAvailability()),
      overridesJson: "[]",
    },
  });

  const updatedUser = await prisma.user.update({
    where: { id: user.id },
    data: { defaultScheduleId: schedule.id },
  });

  sendCreated(response, {
    accessToken: tokenFor(updatedUser.id),
    tokenType: "Bearer",
    user: mapUser(updatedUser),
  });
}

async function updateMe(request, response, user) {
  const body = await readJson(request);
  const updated = await prisma.user.update({
    where: { id: user.id },
    data: clean({
      email: body.email,
      username: body.username,
      name: body.name,
      avatarUrl: body.avatarUrl,
      timeZone: body.timeZone,
    }),
  });
  sendOk(response, mapUser(updated));
}

async function listSchedules(response, user) {
  const schedules = await prisma.schedule.findMany({ where: { ownerId: user.id }, orderBy: { createdAt: "asc" } });
  sendOk(response, { items: schedules.map(mapSchedule) });
}

async function getDefaultSchedule(response, user) {
  const schedule = await prisma.schedule.findFirst({ where: { ownerId: user.id, isDefault: true } });
  if (!schedule) return sendError(response, 404, "not_found", "Default schedule not found.");
  sendOk(response, mapSchedule(schedule));
}

async function getSchedule(response, user, scheduleId) {
  const schedule = await prisma.schedule.findFirst({ where: { id: scheduleId, ownerId: user.id } });
  if (!schedule) return sendError(response, 404, "not_found", "Schedule not found.");
  sendOk(response, mapSchedule(schedule));
}

async function createSchedule(request, response, user) {
  const body = await readJson(request);
  if (body.isDefault) await prisma.schedule.updateMany({ where: { ownerId: user.id }, data: { isDefault: false } });
  const schedule = await prisma.schedule.create({
    data: {
      ownerId: user.id,
      name: body.name || "New schedule",
      timeZone: body.timeZone || user.timeZone,
      isDefault: Boolean(body.isDefault),
      availabilityJson: JSON.stringify(body.availability || defaultAvailability()),
      overridesJson: JSON.stringify(body.overrides || []),
    },
  });
  sendCreated(response, mapSchedule(schedule));
}

async function updateSchedule(request, response, user, scheduleId) {
  const body = await readJson(request);
  const schedule = await prisma.schedule.findFirst({ where: { id: scheduleId, ownerId: user.id } });
  if (!schedule) return sendError(response, 404, "not_found", "Schedule not found.");

  if (body.isDefault) await prisma.schedule.updateMany({ where: { ownerId: user.id }, data: { isDefault: false } });
  const updated = await prisma.schedule.update({
    where: { id: scheduleId },
    data: clean({
      name: body.name,
      timeZone: body.timeZone,
      isDefault: body.isDefault,
      availabilityJson: body.availability ? JSON.stringify(body.availability) : undefined,
      overridesJson: body.overrides ? JSON.stringify(body.overrides) : undefined,
    }),
  });
  sendOk(response, mapSchedule(updated));
}

async function deleteSchedule(response, user, scheduleId) {
  const schedule = await prisma.schedule.findFirst({ where: { id: scheduleId, ownerId: user.id } });
  if (!schedule) return sendError(response, 404, "not_found", "Schedule not found.");
  const attachedEventTypes = await prisma.eventType.count({ where: { scheduleId } });
  if (attachedEventTypes > 0) return sendError(response, 409, "conflict", "Schedule is used by event types.");
  await prisma.schedule.delete({ where: { id: scheduleId } });
  sendNoContent(response);
}

async function listEventTypes(response, user, searchParams) {
  const includeHidden = searchParams.get("includeHidden") === "true";
  const eventTypes = await prisma.eventType.findMany({
    where: { ownerId: user.id, ...(includeHidden ? {} : { hidden: false }) },
    include: { owner: true },
    orderBy: { createdAt: "asc" },
  });
  sendOk(response, { items: eventTypes.map(mapEventType) });
}

async function getEventType(response, user, eventTypeId) {
  const eventType = await prisma.eventType.findFirst({ where: { id: eventTypeId, ownerId: user.id }, include: { owner: true } });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");
  sendOk(response, mapEventType(eventType));
}

async function createEventType(request, response, user) {
  const body = await readJson(request);
  const scheduleId = body.scheduleId || user.defaultScheduleId;
  if (!scheduleId) return sendError(response, 400, "validation_error", "scheduleId is required.");

  const schedule = await prisma.schedule.findFirst({ where: { id: scheduleId, ownerId: user.id } });
  if (!schedule) return sendError(response, 404, "not_found", "Schedule not found.");

  const eventType = await prisma.eventType.create({
    data: {
      ownerId: user.id,
      scheduleId,
      title: body.title || "New event",
      slug: body.slug,
      description: body.description,
      durationMinutes: Number(body.durationMinutes || 30),
      slotIntervalMinutes: body.slotIntervalMinutes,
      minimumBookingNoticeMinutes: body.minimumBookingNoticeMinutes,
      beforeEventBufferMinutes: body.beforeEventBufferMinutes,
      afterEventBufferMinutes: body.afterEventBufferMinutes,
      confirmationPolicyType: body.confirmationPolicy?.type || "automatic",
      blockSlotBeforeConfirmation: Boolean(body.confirmationPolicy?.blockSlotBeforeConfirmation),
      hidden: Boolean(body.hidden),
      bookingUrl: `/${user.username}/${body.slug}`,
    },
    include: { owner: true },
  });
  sendCreated(response, mapEventType(eventType));
}

async function updateEventType(request, response, user, eventTypeId) {
  const body = await readJson(request);
  const eventType = await prisma.eventType.findFirst({ where: { id: eventTypeId, ownerId: user.id } });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");

  const updated = await prisma.eventType.update({
    where: { id: eventTypeId },
    data: clean({
      scheduleId: body.scheduleId,
      title: body.title,
      slug: body.slug,
      description: body.description,
      durationMinutes: body.durationMinutes,
      slotIntervalMinutes: body.slotIntervalMinutes,
      minimumBookingNoticeMinutes: body.minimumBookingNoticeMinutes,
      beforeEventBufferMinutes: body.beforeEventBufferMinutes,
      afterEventBufferMinutes: body.afterEventBufferMinutes,
      confirmationPolicyType: body.confirmationPolicy?.type,
      blockSlotBeforeConfirmation: body.confirmationPolicy?.blockSlotBeforeConfirmation,
      hidden: body.hidden,
      bookingUrl: body.slug ? `/${user.username}/${body.slug}` : undefined,
    }),
    include: { owner: true },
  });
  sendOk(response, mapEventType(updated));
}

async function deleteEventType(response, user, eventTypeId) {
  const eventType = await prisma.eventType.findFirst({ where: { id: eventTypeId, ownerId: user.id } });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");
  await prisma.eventType.delete({ where: { id: eventTypeId } });
  sendNoContent(response);
}

async function getPublicEventType(response, username, slug, searchParams) {
  const eventType = await prisma.eventType.findFirst({
    where: { slug, owner: { username }, hidden: false },
    include: { owner: true },
  });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");

  if (searchParams.get("shareToken")) {
    const shareLink = await prisma.shareLink.findUnique({ where: { token: searchParams.get("shareToken") } });
    if (!shareLink || shareLink.eventTypeId !== eventType.id) return sendError(response, 404, "not_found", "Share link not found.");
    if (isShareLinkExpired(shareLink)) return sendError(response, 410, "link_expired", "Share link is expired.");
  }

  sendOk(response, mapPublicEventType(eventType));
}

async function listShareLinks(response, user, eventTypeId) {
  const eventType = await prisma.eventType.findFirst({ where: { id: eventTypeId, ownerId: user.id } });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");
  const links = await prisma.shareLink.findMany({ where: { eventTypeId }, orderBy: { createdAt: "desc" } });
  sendOk(response, { items: links.map(mapShareLink) });
}

async function createShareLink(request, response, user, eventTypeId) {
  const body = await readJson(request);
  const eventType = await prisma.eventType.findFirst({ where: { id: eventTypeId, ownerId: user.id }, include: { owner: true } });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");
  const token = randomToken();
  const link = await prisma.shareLink.create({
    data: {
      eventTypeId,
      token,
      bookingUrl: `/${eventType.owner.username}/${eventType.slug}?shareToken=${token}`,
      recipientEmail: body.recipientEmail,
      expiresAt: body.expiresAt ? new Date(body.expiresAt) : undefined,
      maxUsageCount: body.maxUsageCount,
    },
  });
  sendCreated(response, mapShareLink(link));
}

async function deleteShareLink(response, user, eventTypeId, shareLinkId) {
  const eventType = await prisma.eventType.findFirst({ where: { id: eventTypeId, ownerId: user.id } });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");
  const link = await prisma.shareLink.findFirst({ where: { id: shareLinkId, eventTypeId } });
  if (!link) return sendError(response, 404, "not_found", "Share link not found.");
  await prisma.shareLink.delete({ where: { id: shareLinkId } });
  sendNoContent(response);
}

async function getPublicShareLink(response, token) {
  const link = await prisma.shareLink.findUnique({ where: { token }, include: { eventType: { include: { owner: true } } } });
  if (!link) return sendError(response, 404, "not_found", "Share link not found.");
  const remainingUsageCount = link.maxUsageCount == null ? undefined : Math.max(link.maxUsageCount - link.usageCount, 0);
  sendOk(response, {
    token: link.token,
    eventType: mapPublicEventType(link.eventType),
    isExpired: isShareLinkExpired(link),
    expiresAt: link.expiresAt,
    remainingUsageCount,
  });
}

async function getOwnedSlots(response, user, searchParams) {
  const eventType = await prisma.eventType.findFirst({
    where: { id: searchParams.get("eventTypeId") ?? "", ownerId: user.id },
    include: { schedule: true, bookings: true },
  });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");
  sendOk(response, buildSlotsResponse(eventType, searchParams));
}

async function getPublicSlots(response, searchParams) {
  const eventType = await prisma.eventType.findFirst({
    where: {
      slug: searchParams.get("eventTypeSlug") ?? "",
      hidden: false,
      owner: { username: searchParams.get("username") ?? "" },
    },
    include: { schedule: true, bookings: true, owner: true },
  });
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");

  const shareToken = searchParams.get("shareToken");
  if (shareToken) {
    const link = await prisma.shareLink.findUnique({ where: { token: shareToken } });
    if (!link || link.eventTypeId !== eventType.id) return sendError(response, 404, "not_found", "Share link not found.");
    if (isShareLinkExpired(link)) return sendError(response, 410, "link_expired", "Share link is expired.");
  }

  sendOk(response, buildSlotsResponse(eventType, searchParams));
}

async function createBooking(request, response) {
  const body = await readJson(request);
  const eventType = await resolveEventTypeForBooking(body);
  if (!eventType) return sendError(response, 404, "not_found", "Event type not found.");

  if (body.shareToken) {
    const link = await prisma.shareLink.findUnique({ where: { token: body.shareToken } });
    if (!link || link.eventTypeId !== eventType.id) return sendError(response, 404, "not_found", "Share link not found.");
    if (isShareLinkExpired(link)) return sendError(response, 410, "link_expired", "Share link is expired.");
    await prisma.shareLink.update({ where: { id: link.id }, data: { usageCount: { increment: 1 } } });
  }

  const start = new Date(body.start);
  const durationMinutes = Number(body.durationMinutes || eventType.durationMinutes);
  const end = new Date(start.getTime() + durationMinutes * 60_000);
  const status = eventType.confirmationPolicyType === "automatic" ? "confirmed" : `pending_${eventType.confirmationPolicyType}`;

  const booking = await prisma.booking.create({
    data: {
      uid: `booking_${randomUUID().slice(0, 8)}`,
      eventTypeId: eventType.id,
      ownerId: eventType.ownerId,
      title: eventType.title,
      description: eventType.description,
      status,
      start,
      end,
      durationMinutes,
      attendeeName: body.attendee.name,
      attendeeEmail: body.attendee.email,
      attendeeTimeZone: body.attendee.timeZone,
      attendeeToken: randomToken(),
      shareToken: body.shareToken,
    },
    include: { eventType: true, owner: true },
  });
  sendCreated(response, mapBooking(booking));
}

async function listBookings(response, user, searchParams) {
  const bookings = await prisma.booking.findMany({
    where: clean({
      ownerId: user.id,
      status: searchParams.get("status") || undefined,
    }),
    include: { owner: true, eventType: true },
    orderBy: { start: "asc" },
  });
  sendOk(response, { items: bookings.map(mapBooking) });
}

async function getBooking(response, user, bookingUid) {
  const booking = await prisma.booking.findFirst({ where: { uid: bookingUid, ownerId: user.id }, include: { owner: true, eventType: true } });
  if (!booking) return sendError(response, 404, "not_found", "Booking not found.");
  sendOk(response, mapBooking(booking));
}

async function updateBookingStatus(response, user, bookingUid, status, body = {}) {
  const booking = await prisma.booking.findFirst({ where: { uid: bookingUid, ownerId: user.id } });
  if (!booking) return sendError(response, 404, "not_found", "Booking not found.");
  const updated = await prisma.booking.update({
    where: { uid: bookingUid },
    data: clean({
      status,
      rejectionReason: status === "declined" ? body.reason || "Declined by host" : undefined,
      cancellationReason: status === "cancelled" ? body.reason || "Cancelled by host" : undefined,
    }),
    include: { owner: true, eventType: true },
  });
  sendOk(response, mapBooking(updated));
}

async function confirmAttendee(response, bookingUid, searchParams) {
  const booking = await prisma.booking.findUnique({ where: { uid: bookingUid } });
  if (!booking) return sendError(response, 404, "not_found", "Booking not found.");
  if (booking.attendeeToken !== searchParams.get("token")) return sendError(response, 410, "link_expired", "Invalid attendee token.");
  const updated = await prisma.booking.update({
    where: { uid: bookingUid },
    data: { status: "confirmed", attendeeConfirmedAt: new Date() },
    include: { owner: true, eventType: true },
  });
  sendOk(response, mapBooking(updated));
}

async function resolveEventTypeForBooking(body) {
  if (body.eventTypeId) {
    return prisma.eventType.findUnique({ where: { id: body.eventTypeId } });
  }
  if (body.username && body.eventTypeSlug) {
    return prisma.eventType.findFirst({
      where: { slug: body.eventTypeSlug, hidden: false, owner: { username: body.username } },
    });
  }
  if (body.shareToken) {
    const link = await prisma.shareLink.findUnique({ where: { token: body.shareToken } });
    if (!link) return null;
    return prisma.eventType.findUnique({ where: { id: link.eventTypeId } });
  }
  return null;
}

async function requireUser(request, response) {
  const header = request.headers.authorization ?? "";
  const match = header.match(/^Bearer\s+mock-token-(.+)$/);
  if (!match) {
    sendError(response, 401, "unauthorized", "Bearer token is required.");
    return null;
  }

  const user = await prisma.user.findUnique({ where: { id: match[1] } });
  if (!user) {
    sendError(response, 401, "unauthorized", "Invalid token.");
    return null;
  }

  return user;
}

function buildSlotsResponse(eventType, searchParams) {
  const start = parseLocalDate(searchParams.get("start"));
  const end = parseLocalDate(searchParams.get("end"));
  const durationMinutes = Number(searchParams.get("durationMinutes") || eventType.durationMinutes);
  const timeZone = searchParams.get("timeZone") || eventType.schedule.timeZone;
  const availability = parseJson(eventType.schedule.availabilityJson, []);
  const days = [];

  for (let cursor = start; cursor <= end; cursor = addDays(cursor, 1)) {
    const date = toLocalDate(cursor);
    const weekday = weekdayByIndex[cursor.getUTCDay()];
    const rules = availability.filter((rule) => rule.days.includes(weekday));
    const slots = [];

    for (const rule of rules) {
      let slotStart = withLocalTime(cursor, rule.startTime);
      const windowEnd = withLocalTime(cursor, rule.endTime);

      while (slotStart.getTime() + durationMinutes * 60_000 <= windowEnd.getTime()) {
        const slotEnd = new Date(slotStart.getTime() + durationMinutes * 60_000);
        slots.push({
          start: slotStart.toISOString(),
          end: slotEnd.toISOString(),
          available: isSlotAvailable(slotStart, slotEnd, eventType.bookings),
        });
        slotStart = new Date(slotStart.getTime() + (eventType.slotIntervalMinutes || durationMinutes) * 60_000);
      }
    }

    days.push({ date, slots });
  }

  return { timeZone, days };
}

function isSlotAvailable(start, end, bookings) {
  return !bookings.some((booking) => {
    if (["cancelled", "declined"].includes(booking.status)) return false;
    return start < booking.end && end > booking.start;
  });
}

function mapUser(user) {
  return {
    id: user.id,
    email: user.email,
    username: user.username,
    name: user.name,
    avatarUrl: user.avatarUrl,
    timeZone: user.timeZone,
    defaultScheduleId: user.defaultScheduleId,
    createdAt: user.createdAt,
    updatedAt: user.updatedAt,
  };
}

function mapPublicUser(user) {
  return {
    id: user.id,
    username: user.username,
    name: user.name,
    avatarUrl: user.avatarUrl,
    timeZone: user.timeZone,
  };
}

function mapSchedule(schedule) {
  return {
    id: schedule.id,
    ownerId: schedule.ownerId,
    name: schedule.name,
    timeZone: schedule.timeZone,
    isDefault: schedule.isDefault,
    availability: parseJson(schedule.availabilityJson, []),
    overrides: parseJson(schedule.overridesJson, []),
    createdAt: schedule.createdAt,
    updatedAt: schedule.updatedAt,
  };
}

function mapEventType(eventType) {
  return {
    id: eventType.id,
    ownerId: eventType.ownerId,
    title: eventType.title,
    slug: eventType.slug,
    description: eventType.description,
    durationMinutes: eventType.durationMinutes,
    scheduleId: eventType.scheduleId,
    slotIntervalMinutes: eventType.slotIntervalMinutes,
    minimumBookingNoticeMinutes: eventType.minimumBookingNoticeMinutes,
    beforeEventBufferMinutes: eventType.beforeEventBufferMinutes,
    afterEventBufferMinutes: eventType.afterEventBufferMinutes,
    confirmationPolicy: {
      type: eventType.confirmationPolicyType,
      blockSlotBeforeConfirmation: eventType.blockSlotBeforeConfirmation,
    },
    hidden: eventType.hidden,
    bookingUrl: eventType.bookingUrl,
    createdAt: eventType.createdAt,
    updatedAt: eventType.updatedAt,
  };
}

function mapPublicEventType(eventType) {
  return {
    id: eventType.id,
    owner: mapPublicUser(eventType.owner),
    title: eventType.title,
    slug: eventType.slug,
    description: eventType.description,
    durationMinutes: eventType.durationMinutes,
    slotIntervalMinutes: eventType.slotIntervalMinutes,
    minimumBookingNoticeMinutes: eventType.minimumBookingNoticeMinutes,
    confirmationPolicy: {
      type: eventType.confirmationPolicyType,
      blockSlotBeforeConfirmation: eventType.blockSlotBeforeConfirmation,
    },
    bookingUrl: eventType.bookingUrl,
  };
}

function mapShareLink(link) {
  return {
    id: link.id,
    eventTypeId: link.eventTypeId,
    token: link.token,
    bookingUrl: link.bookingUrl,
    recipientEmail: link.recipientEmail,
    expiresAt: link.expiresAt,
    maxUsageCount: link.maxUsageCount,
    usageCount: link.usageCount,
    isExpired: isShareLinkExpired(link),
    createdAt: link.createdAt,
  };
}

function mapBooking(booking) {
  return {
    id: booking.id,
    uid: booking.uid,
    eventTypeId: booking.eventTypeId,
    owner: mapPublicUser(booking.owner),
    title: booking.title,
    description: booking.description,
    status: booking.status,
    start: booking.start,
    end: booking.end,
    durationMinutes: booking.durationMinutes,
    attendee: {
      name: booking.attendeeName,
      email: booking.attendeeEmail,
      timeZone: booking.attendeeTimeZone,
      confirmedAt: booking.attendeeConfirmedAt,
    },
    shareToken: booking.shareToken,
    meetingUrl: booking.meetingUrl,
    cancellationReason: booking.cancellationReason,
    rejectionReason: booking.rejectionReason,
    createdAt: booking.createdAt,
    updatedAt: booking.updatedAt,
  };
}

function defaultAvailability() {
  return [
    { days: ["monday", "tuesday", "wednesday", "thursday", "friday"], startTime: "09:00", endTime: "12:00" },
    { days: ["monday", "tuesday", "wednesday", "thursday", "friday"], startTime: "13:00", endTime: "18:00" },
  ];
}

function tokenFor(userId) {
  return `mock-token-${userId}`;
}

function randomToken() {
  return randomUUID().replaceAll("-", "");
}

function isShareLinkExpired(link) {
  if (link.expiresAt && link.expiresAt < new Date()) return true;
  if (link.maxUsageCount != null && link.usageCount >= link.maxUsageCount) return true;
  return false;
}

function parseJson(value, fallback) {
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function parseLocalDate(value) {
  if (!value) return new Date();
  return new Date(`${value}T00:00:00.000Z`);
}

function toLocalDate(date) {
  return date.toISOString().slice(0, 10);
}

function addDays(date, days) {
  const next = new Date(date);
  next.setUTCDate(next.getUTCDate() + days);
  return next;
}

function withLocalTime(date, time) {
  const [hour, minute] = time.split(":").map(Number);
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), hour, minute, 0));
}

function clean(input) {
  return Object.fromEntries(Object.entries(input).filter(([, value]) => value !== undefined));
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString("utf8");
  return raw ? JSON.parse(raw) : {};
}

function sendOk(response, data) {
  send(response, 200, { status: "success", data });
}

function sendCreated(response, data) {
  send(response, 201, { status: "success", data });
}

function sendNoContent(response) {
  response.writeHead(204);
  response.end();
}

function sendError(response, statusCode, code, message) {
  send(response, statusCode, { status: "error", error: { code, message } });
}

function send(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  response.end(JSON.stringify(payload));
}

function setCors(response) {
  response.setHeader("access-control-allow-origin", "*");
  response.setHeader("access-control-allow-methods", "GET,POST,PATCH,DELETE,OPTIONS");
  response.setHeader("access-control-allow-headers", "content-type,authorization");
}

function trimTrailingSlash(pathname) {
  return pathname !== "/" && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
}
