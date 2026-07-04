# Calendar Booking

This context describes how hosts expose bookable time and how attendees create bookings. The language below is product language, not API or storage naming.

## Language

**Host**:
A person who offers bookable time through schedules and event types.
_Avoid_: Owner, calendar owner, user when describing the business role

**Attendee**:
A person who requests or holds booked time with a Host.
_Avoid_: Guest, invitee, participant

**Schedule**:
A Host's recurring availability and dated availability changes in one time zone.
_Avoid_: Calendar, working hours

**Availability Rule**:
A recurring local-time interval on one or more weekdays when a Schedule can produce Slots.
_Avoid_: Opening hours, weekly rule

**Availability Override**:
A date-specific change to Schedule availability that either removes or adds available local time.
_Avoid_: Exception, blackout

**Event Type**:
A bookable offering owned by a Host, with a duration, Schedule, visibility, and booking rules.
_Avoid_: Meeting type, service

**Slot**:
A candidate time interval generated for an Event Type from its Schedule and booking rules. A Slot can be available or blocked.
_Avoid_: Time option, time cell

**Booking**:
A request or reservation for one Event Type at a specific time interval with one Attendee.
_Avoid_: Appointment, meeting

**Pending Booking**:
A Booking awaiting confirmation from either the Host or the Attendee, depending on the Confirmation Policy.
_Avoid_: Draft booking, tentative booking

**Confirmed Booking**:
A Booking that no longer requires confirmation and reserves the time.
_Avoid_: Accepted booking

**Declined Booking**:
A Pending Booking rejected by the Host.
_Avoid_: Rejected booking

**Cancelled Booking**:
A Booking that is stopped after creation rather than rejected during Host review.
_Avoid_: Deleted booking

**Confirmation Policy**:
The rule that decides whether a new Booking is immediately confirmed or waits for Host or Attendee confirmation.
_Avoid_: Approval mode

**Booking Window**:
The range of calendar dates in which new Bookings can be created for an Event Type.
_Avoid_: Date filter, date range

**Buffer**:
Time protected before or after a Booking so adjacent Slots are not offered too close to it.
_Avoid_: Padding, gap

**Share Link**:
A tokenized private link that grants booking access to an Event Type and can have expiry or usage limits.
_Avoid_: Invite link, public link

**Share Link Usage**:
One successful Booking created through a Share Link. Viewing or opening the link is not usage.
_Avoid_: View count, click count
