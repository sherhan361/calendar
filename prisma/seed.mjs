import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const availability = [
  { days: ["monday", "tuesday", "wednesday", "thursday", "friday"], startTime: "09:00", endTime: "12:00" },
  { days: ["monday", "tuesday", "wednesday", "thursday", "friday"], startTime: "13:00", endTime: "18:00" },
];

async function main() {
  await prisma.booking.deleteMany();
  await prisma.shareLink.deleteMany();
  await prisma.eventType.deleteMany();
  await prisma.schedule.deleteMany();
  await prisma.user.deleteMany();

  const user = await prisma.user.create({
    data: {
      email: "demo@example.com",
      username: "demo",
      name: "Dmitry Calendar",
      timeZone: "Europe/Moscow",
    },
  });

  const schedule = await prisma.schedule.create({
    data: {
      ownerId: user.id,
      name: "Working hours",
      timeZone: "Europe/Moscow",
      isDefault: true,
      availabilityJson: JSON.stringify(availability),
      overridesJson: "[]",
    },
  });

  await prisma.user.update({
    where: { id: user.id },
    data: { defaultScheduleId: schedule.id },
  });

  const productDiscovery = await prisma.eventType.create({
    data: {
      ownerId: user.id,
      scheduleId: schedule.id,
      title: "Product discovery",
      slug: "product-discovery",
      description: "A focused 30 minute call to align on goals, scope, and next steps.",
      durationMinutes: 30,
      slotIntervalMinutes: 30,
      minimumBookingNoticeMinutes: 60,
      beforeEventBufferMinutes: 0,
      afterEventBufferMinutes: 15,
      confirmationPolicyType: "host",
      blockSlotBeforeConfirmation: true,
      bookingUrl: "/demo/product-discovery",
    },
  });

  await prisma.eventType.create({
    data: {
      ownerId: user.id,
      scheduleId: schedule.id,
      title: "Architecture review",
      slug: "architecture-review",
      description: "A longer technical review for backend design and integration tradeoffs.",
      durationMinutes: 60,
      slotIntervalMinutes: 30,
      minimumBookingNoticeMinutes: 120,
      afterEventBufferMinutes: 15,
      confirmationPolicyType: "automatic",
      bookingUrl: "/demo/architecture-review",
    },
  });

  await prisma.shareLink.create({
    data: {
      eventTypeId: productDiscovery.id,
      token: "demo-product-link-2026",
      bookingUrl: "/demo/product-discovery?shareToken=demo-product-link-2026",
      recipientEmail: "guest@example.com",
      maxUsageCount: 5,
    },
  });

  const now = new Date();
  const tomorrow = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1, 8, 0, 0));
  await prisma.booking.create({
    data: {
      uid: "booking_demo_pending",
      eventTypeId: productDiscovery.id,
      ownerId: user.id,
      title: productDiscovery.title,
      description: productDiscovery.description,
      status: "pending_host",
      start: tomorrow,
      end: new Date(tomorrow.getTime() + productDiscovery.durationMinutes * 60_000),
      durationMinutes: productDiscovery.durationMinutes,
      attendeeName: "Alex Guest",
      attendeeEmail: "alex@example.com",
      attendeeTimeZone: "Europe/Moscow",
      attendeeToken: "attendee_demo_pending_token",
      shareToken: "demo-product-link-2026",
    },
  });
}

main()
  .then(async () => {
    await prisma.$disconnect();
    console.log("Mock database seeded.");
  })
  .catch(async (error) => {
    console.error(error);
    await prisma.$disconnect();
    process.exit(1);
  });
