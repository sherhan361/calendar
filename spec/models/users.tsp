namespace Calendar;

model User {
  id: Uuid;
  email: Email;
  username: Username;
  name: string;
  avatarUrl?: string;
  timeZone: TimeZone;
  defaultScheduleId?: Uuid;
  createdAt: utcDateTime;
  updatedAt: utcDateTime;
}

model PublicUser {
  id: Uuid;
  username: Username;
  name: string;
  avatarUrl?: string;
  timeZone: TimeZone;
}

model RegisterRequest {
  email: Email;
  username: Username;
  name: string;
  password: string;
  timeZone: TimeZone;
}

model LoginRequest {
  email: Email;
  password: string;
}

model AuthSession {
  accessToken: string;
  tokenType: "Bearer";
  user: User;
}

model UpdateMeRequest {
  email?: Email;
  username?: Username;
  name?: string;
  avatarUrl?: string;
  timeZone?: TimeZone;
}
