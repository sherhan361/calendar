namespace Calendar;

model Slot {
  start: utcDateTime;
  end: utcDateTime;
  available: boolean;
}

model SlotsByDate {
  date: LocalDate;
  slots: Slot[];
}

model SlotsResponse {
  timeZone: TimeZone;
  days: SlotsByDate[];
}
