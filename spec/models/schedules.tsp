namespace Calendar;

enum Weekday {
  monday: "monday",
  tuesday: "tuesday",
  wednesday: "wednesday",
  thursday: "thursday",
  friday: "friday",
  saturday: "saturday",
  sunday: "sunday",
}

model AvailabilityRule {
  id: Uuid;
  days: Weekday[];
  startTime: LocalTime;
  endTime: LocalTime;
}

model AvailabilityRuleInput {
  days: Weekday[];
  startTime: LocalTime;
  endTime: LocalTime;
}

model AvailabilityOverride {
  id: Uuid;
  date: LocalDate;
  startTime?: LocalTime;
  endTime?: LocalTime;
  unavailable: boolean;
}

model AvailabilityOverrideInput {
  date: LocalDate;
  startTime?: LocalTime;
  endTime?: LocalTime;
  unavailable?: boolean;
}

model Schedule {
  id: Uuid;
  ownerId: Uuid;
  name: string;
  timeZone: TimeZone;
  isDefault: boolean;
  availability: AvailabilityRule[];
  overrides: AvailabilityOverride[];
  createdAt: utcDateTime;
  updatedAt: utcDateTime;
}

model CreateScheduleRequest {
  name: string;
  timeZone: TimeZone;
  isDefault?: boolean;
  availability: AvailabilityRuleInput[];
  overrides?: AvailabilityOverrideInput[];
}

model UpdateScheduleRequest {
  name?: string;
  timeZone?: TimeZone;
  isDefault?: boolean;
  availability?: AvailabilityRuleInput[];
  overrides?: AvailabilityOverrideInput[];
}
