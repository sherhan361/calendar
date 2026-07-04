namespace Calendar;

model ShareLink {
  id: Uuid;
  eventTypeId: Uuid;
  token: PublicToken;
  bookingUrl: string;
  recipientEmail?: Email;
  expiresAt?: utcDateTime;
  maxUsageCount?: int32;
  usageCount: int32;
  isExpired: boolean;
  createdAt: utcDateTime;
}

model CreateShareLinkRequest {
  recipientEmail?: Email;
  expiresAt?: utcDateTime;
  maxUsageCount?: int32;
}

model PublicShareLink {
  token: PublicToken;
  eventType: PublicEventType;
  isExpired: boolean;
  expiresAt?: utcDateTime;
  remainingUsageCount?: int32;
}
