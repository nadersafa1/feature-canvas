# Pinewood Class Booking Flows

Members book a place in a climbing class from the app; the front desk runs the week on the web; coaches take attendance on their phone. Six stories make it usable, nine make it complete.

Sample world: see WORLD.md. Now = Mon 12 Oct 2026, 9:15 AM.

## Decisions

- **#1 Capacity** (agreed). A hard cap for members; the desk and owner may go over with a reason.
- **#2 Clashes** (agreed). A copied class that clashes is flagged, never moved automatically.
- **#3 Cancel cut-off** (agreed). Free to cancel until 12 h before the start. A later cancel still frees the place but counts as a No-show.
- **#4 Reminder** (assumed). One push 2 h before the start; no email in v1.
- **#5 Waitlist offer** (assumed). A freed place is held for the next person for 30 minutes.

## B1 · Run the week

The desk publishes classes and checks members in.

- Gives: Classes exist on a schedule with coaches, walls and capacities; the desk books and checks in by hand.
- Needs first: nothing
- Screens: W01, W02

### B1.1 Week schedule (M · Web)

As a front desk, I want one schedule screen for the whole week, so that I can see every class, wall and coach at once.

- [ ] Seven days by wall, with draft and published classes told apart
- [ ] Opens on the current week

### B1.2 Copy last week (M · Web · decisions #2)

As a front desk, I want to copy last week's classes as drafts, so that I don't rebuild the same week by hand.

- [ ] Copies as drafts, never published
- [ ] A coach or wall clash is flagged on the class, never silently moved

### B1.3 Publish (S · Web)

As a front desk, I want to publish drafts in one press, so that members can book them.

- [ ] Publishing counts the drafts it will publish
- [ ] A class with a clash can't be published

### B1.4 Check in at the door (M · Web)

As a front desk, I want to tick members off the roster, so that the coach starts on time.

- [ ] Came and No-show per member
- [ ] The coach's app shows the same marks


## B2 · Members book

Members find and book a class themselves.

- Gives: Booking moves from the phone line to the app; the desk only handles exceptions.
- Needs first: B1
- Screens: W02, M01, M02, M03

### B2.1 Browse classes (M · App)

As a member, I want to see this week's classes by level, so that I find one that fits.

- [ ] Level chips and a day strip
- [ ] Places left on every card; Full when none

### B2.2 Book a place (L · App, Web · decisions #1, #3)

As a member, I want to book a place in one tap, so that I'm sure I'm in.

- [ ] The cancel cut-off is shown before booking (#3)
- [ ] Capacity is a hard cap for members (#1)
- [ ] The desk can book on a member's behalf

### B2.3 My bookings (S · App)

As a member, I want my upcoming and past classes in one list, so that I know where I'm due.

- [ ] Upcoming first, with Cancel until the cut-off
- [ ] Past shows Came or No-show

### B2.4 Reminder (S · App · decisions #4)

As a member, I want a reminder before class, so that I don't forget it.

- [ ] Push 2 h before the start (#4)
- [ ] Opens the class


## B3 · Waitlists

A full class still takes interest.

- Gives: Freed places go to the next person in line instead of staying empty.
- Needs first: B2
- Screens: M02

### B3.1 Join a waitlist (M · App · decisions #5)

As a member, I want to join the waitlist of a full class, so that I get a place if one frees up.

- [ ] Shows my place in line
- [ ] A freed place is offered for 30 minutes, then moves on (#5)


## B4 · Later (parking lot)

Parked until the core is in use.

- Gives: Nothing yet.
- Needs first: nothing
- Screens: none

### B4.1 Class packs (L · App)

As a member, I want to buy ten classes at once, so that each class costs less.

- [ ] Needs online payment first

## Screens

- **W01 Week schedule** (Web; B1.1, B1.2, B1.3). Desk › Schedule, week of 12 Oct. Seven day columns with class blocks; drafts dashed. The Wed 6:00 PM Intro to Bouldering is selected (8 of 10 at 9:15 AM). Toolbar: Copy last week, Publish 2 drafts; the Thu Technique Lab draft is held back by its clash with Youth Climb Club.
- **W02 Class roster and check-in** (Web; B1.4, B2.2). One class at 9:40 AM: Wed 6:00 PM Intro to Bouldering, Maya Chen, Wall B, 9 of 10. Roster table with Came / No-show toggles, Book a member dialog open: Priya phones to book herself and Dev, which takes the class to 11 of 10, so the reason field shows (#1).
- **M01 Classes this week** (App; B2.1). Classes tab: level chips (All, Beginner, Intermediate), day strip Mon–Sun with Wed selected, class cards with time, coach, places left, Full chip with Join waitlist.
- **M02 Book a class** (App; B2.2, B3.1). Class detail for Wed 6:00 PM Intro to Bouldering: coach, wall, places left, price 18 USD, cut-off line 'Free to cancel until Wed 6:00 AM', Book a place button. Moment: 9:20 AM, 8 of 10 booked, 2 places left.
- **M03 My bookings** (App; B2.3, B2.4). Profile › My bookings: Upcoming (Wed intro with Cancel, free until 6:00 AM), Past (Came, No-show chips).
