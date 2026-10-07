# Single source for the "Pinewood Class Booking" canvas. Plain data only; build.py renders it.
# Schema: ../../SPEC.md. Sample world: WORLD.md (never contradict it).

CANVAS = {
    "title": "Pinewood Class Booking Flows",
    "product": "Pinewood",
    "feature": "Class booking",
    "lead": "Members book a place in a climbing class from the app; the front desk runs the week on the web; coaches take attendance on their phone. Six stories make it usable, nine make it complete.",
    "now": "Mon 12 Oct 2026, 9:15 AM",
    "model_title": "How a class is built",
    "roadmap_lead": "Three stages, each deployable on its own. The desk track ships first so classes exist before anyone can book them.",
}

BRAND = {}  # keys: ink, accent, feature, ground, serif, sans. Empty = the default kit.

SURFACES = [
    {"id": "web", "name": "Web", "kind": "web", "color": "#0E2F3E", "page": "Web · front desk",
     "nav": ["Today/", "Front desk", "Check-in", "Classes/", "Schedule", "Class types", "Members/", "Members"]},
    {"id": "app", "name": "App", "kind": "phone", "color": "#8FA123", "page": "Mobile · member and coach",
     "nav": ["Home", "Classes", "Profile"]},
]

ROLES = [
    {"id": "owner", "name": "Gym owner", "persona": "Dana Reyes", "surfaces": ["web"],
     "does": "Sets class types and prices, and reads how full the week is."},
    {"id": "desk", "name": "Front desk", "persona": "Leo Park", "surfaces": ["web"],
     "does": "Publishes the week's classes, books members in by phone and checks them in."},
    {"id": "coach", "name": "Coach", "persona": "Maya Chen", "surfaces": ["app"],
     "does": "Sees today's classes and their rosters; marks who came."},
    {"id": "member", "name": "Member", "persona": "Sam Okafor", "surfaces": ["app"],
     "does": "Finds a class that fits, books a place and cancels in time if plans change."},
]

ENTITIES = [
    {"name": "Class type", "what": "A kind of class the gym teaches, with its level, length and price.",
     "facts": ["Intro to Bouldering · Beginner · 60 min · 18 USD", "Owner-only to create or reprice"],
     "links": ["Has many classes"]},
    {"name": "Class", "what": "One dated meeting of a class type, with a coach, a wall and a capacity.",
     "facts": ["Capacity is a hard cap; the waitlist is separate", "Cancelling a class frees every place and tells every member"],
     "links": ["Has many bookings", "Taught by one coach"]},
    {"name": "Booking", "what": "One member's place in one class.",
     "facts": ["Free to cancel until 12 h before the start (#3)", "Marked Came or No-show by the coach"],
     "links": ["Belongs to a member and a class"]},
]

PERMISSIONS = [
    ("Set up", [
        ("Create or reprice class types", {"owner": "Yes"}),
        ("Publish, move or cancel a class", {"owner": "Yes", "desk": "Yes"}),
    ]),
    ("Bookings", [
        ("Book a place", {"owner": "Yes", "desk": "On a member's behalf", "member": "Yes"}),
        ("Book over capacity", {"owner": "Yes", "desk": "Yes"}),
        ("Mark attendance", {"owner": "Yes", "desk": "Yes", "coach": "Own classes"}),
    ]),
]

JOURNEYS = [
    {"role": "member", "title": "Book Wednesday's intro class", "steps": [
        ("Open Classes", "M01"), ("Filter: Beginner, this week", "M01 · B2.1"), ("Pick Wed 6:00 PM", "M02"),
        ("Book a place", "M02 · B2.2"), ("Reminder 2 h before", "B2.4"), ("Climb", None)]},
    {"role": "desk", "title": "Publish next week", "steps": [
        ("Open Schedule", "W01"), ("Copy this week", "W01 · B1.2"), ("Fix one clash", "W01 · B1.2"), ("Publish", "W01 · B1.3")]},
]

LIFECYCLES = {
    "lead": "Every record that changes over time, its states, and who moves it. Nothing is hard-deleted.",
    "lanes": [
        {"tag": "Class", "title": "One dated meeting", "nodes": [
            ("c1", 0, 0, "state", "Draft", "desk only"), ("c2", 0, 1, "state", "Published", "members can book"),
            ("c3", 0, 2, "state", "Done", "attendance taken"), ("c4", 1, 1, "state", "Cancelled", "everyone told")],
         "edges": [("c1", "c2", "desk"), ("c2", "c3", "coach"), ("c2", "c4", "desk")]},
        {"tag": "Booking", "title": "One member's place", "nodes": [
            ("b1", 0, 0, "state", "Booked"), ("b2", 0, 1, "state", "Came"), ("b3", 1, 0, "state", "Cancelled", "free until 12 h"),
            ("b4", 1, 1, "state", "No-show")],
         "edges": [("b1", "b2", "coach"), ("b1", "b3", "member"), ("b1", "b4", "coach")]},
    ],
}

FLOWS = [
    {"id": "F1", "role": "member", "title": "Sam, member",
     "lead": "Books from the app in under a minute and is never surprised by a fee: the cancel cut-off is shown before the place is taken.",
     "lanes": [
         {"tag": "B2", "title": "Book a place", "nodes": [
             ("a1", 0, 0, "step", "Classes tab", "M01 · B2.1"),
             ("a2", 0, 1, "step", "Pick a class", "M02"),
             ("a3", 0, 2, "decision", "A place left?"),
             ("a4", 0, 3, "step", "Book; cut-off shown", "M02 · B2.2"),
             ("a5", 0, 4, "end", "In My bookings", "M03 · B2.3"),
             ("a6", 1, 2, "step", "Join the waitlist", "M02 · B3.1"),
             ("a7", 1, 4, "push", "Reminder 2 h before", "B2.4")],
          "edges": [("a1", "a2"), ("a2", "a3"), ("a3", "a4", "yes"), ("a4", "a5"), ("a3", "a6", "no"), ("a5", "a7")]},
     ]},
    {"id": "F2", "role": "desk", "title": "Leo, front desk",
     "lead": "Runs the week from one schedule screen: copies last week, fixes clashes, publishes, then checks people in at the door.",
     "lanes": [
         {"tag": "B1", "title": "Publish the week", "nodes": [
             ("p1", 0, 0, "step", "Schedule", "W01 · B1.1"),
             ("p2", 0, 1, "step", "Copy last week", "W01 · B1.2"),
             ("p3", 0, 2, "decision", "Any clash?"),
             ("p4", 0, 3, "step", "Publish", "W01 · B1.3"),
             ("p5", 0, 4, "end", "Members can book"),
             ("p6", 1, 2, "step", "Move to a free wall", "W01 · B1.2")],
          "edges": [("p1", "p2"), ("p2", "p3"), ("p3", "p4", "no"), ("p4", "p5"), ("p3", "p6", "yes"), ("p6", "p4")]},
     ]},
]

SCREENS = [
    {"id": "W01", "slug": "Schedule", "title": "Week schedule", "surface": "web", "stories": ["B1.1", "B1.2", "B1.3"],
     "brief": "Desk › Schedule, week of 12 Oct. Seven day columns with class blocks; drafts dashed. The Wed 6:00 PM Intro to Bouldering is selected (8 of 10 at 9:15 AM). Toolbar: Copy last week, Publish 2 drafts; the Thu Technique Lab draft is held back by its clash with Youth Climb Club."},
    {"id": "W02", "slug": "Roster", "title": "Class roster and check-in", "surface": "web", "stories": ["B1.4", "B2.2"],
     "brief": "One class at 9:40 AM: Wed 6:00 PM Intro to Bouldering, Maya Chen, Wall B, 9 of 10. Roster table with Came / No-show toggles, Book a member dialog open: Priya phones to book herself and Dev, which takes the class to 11 of 10, so the reason field shows (#1)."},
    {"id": "M01", "slug": "Classes", "title": "Classes this week", "surface": "app", "stories": ["B2.1"],
     "brief": "Classes tab: level chips (All, Beginner, Intermediate), day strip Mon–Sun with Wed selected, class cards with time, coach, places left, Full chip with Join waitlist."},
    {"id": "M02", "slug": "BookClass", "title": "Book a class", "surface": "app", "stories": ["B2.2", "B3.1"],
     "brief": "Class detail for Wed 6:00 PM Intro to Bouldering: coach, wall, places left, price 18 USD, cut-off line 'Free to cancel until Wed 6:00 AM', Book a place button. Moment: 9:20 AM, 8 of 10 booked, 2 places left."},
    {"id": "M03", "slug": "MyBookings", "title": "My bookings", "surface": "app", "stories": ["B2.3", "B2.4"],
     "brief": "Profile › My bookings: Upcoming (Wed intro with Cancel, free until 6:00 AM), Past (Came, No-show chips)."},
]

STAGES = [
    {"id": "B1", "name": "Run the week", "track": "Desk", "after": [],
     "tagline": "The desk publishes classes and checks members in.",
     "gets": "Classes exist on a schedule with coaches, walls and capacities; the desk books and checks in by hand.",
     "stories": [
         {"id": "B1.1", "size": "M", "surfaces": ["web"], "title": "Week schedule", "as": "desk",
          "want": "one schedule screen for the whole week", "so": "I can see every class, wall and coach at once",
          "accept": ["Seven days by wall, with draft and published classes told apart", "Opens on the current week"]},
         {"id": "B1.2", "size": "M", "surfaces": ["web"], "title": "Copy last week", "as": "desk",
          "want": "to copy last week's classes as drafts", "so": "I don't rebuild the same week by hand",
          "accept": ["Copies as drafts, never published", "A coach or wall clash is flagged on the class, never silently moved"],
          "decisions": [2]},
         {"id": "B1.3", "size": "S", "surfaces": ["web"], "title": "Publish", "as": "desk",
          "want": "to publish drafts in one press", "so": "members can book them",
          "accept": ["Publishing counts the drafts it will publish", "A class with a clash can't be published"]},
         {"id": "B1.4", "size": "M", "surfaces": ["web"], "title": "Check in at the door", "as": "desk",
          "want": "to tick members off the roster", "so": "the coach starts on time",
          "accept": ["Came and No-show per member", "The coach's app shows the same marks"]},
     ]},
    {"id": "B2", "name": "Members book", "track": "Members", "after": ["B1"],
     "tagline": "Members find and book a class themselves.",
     "gets": "Booking moves from the phone line to the app; the desk only handles exceptions.",
     "stories": [
         {"id": "B2.1", "size": "M", "surfaces": ["app"], "title": "Browse classes", "as": "member",
          "want": "to see this week's classes by level", "so": "I find one that fits",
          "accept": ["Level chips and a day strip", "Places left on every card; Full when none"]},
         {"id": "B2.2", "size": "L", "surfaces": ["app", "web"], "title": "Book a place", "as": "member",
          "want": "to book a place in one tap", "so": "I'm sure I'm in",
          "accept": ["The cancel cut-off is shown before booking (#3)", "Capacity is a hard cap for members (#1)", "The desk can book on a member's behalf"],
          "decisions": [1, 3]},
         {"id": "B2.3", "size": "S", "surfaces": ["app"], "title": "My bookings", "as": "member",
          "want": "my upcoming and past classes in one list", "so": "I know where I'm due",
          "accept": ["Upcoming first, with Cancel until the cut-off", "Past shows Came or No-show"]},
         {"id": "B2.4", "size": "S", "surfaces": ["app"], "title": "Reminder", "as": "member",
          "want": "a reminder before class", "so": "I don't forget it", "screen": False,
          "accept": ["Push 2 h before the start (#4)", "Opens the class"], "decisions": [4]},
     ]},
    {"id": "B3", "name": "Waitlists", "track": "Members", "after": ["B2"],
     "tagline": "A full class still takes interest.",
     "gets": "Freed places go to the next person in line instead of staying empty.",
     "stories": [
         {"id": "B3.1", "size": "M", "surfaces": ["app"], "title": "Join a waitlist", "as": "member",
          "want": "to join the waitlist of a full class", "so": "I get a place if one frees up",
          "accept": ["Shows my place in line", "A freed place is offered for 30 minutes, then moves on (#5)"],
          "decisions": [5]},
     ]},
    {"id": "B4", "name": "Later", "later": True, "after": [],
     "tagline": "Parked until the core is in use.",
     "gets": "Nothing yet.",
     "stories": [
         {"id": "B4.1", "size": "L", "surfaces": ["app"], "title": "Class packs", "as": "member",
          "want": "to buy ten classes at once", "so": "each class costs less",
          "accept": ["Needs online payment first"]},
     ]},
]

MILESTONES = [
    {"name": "The desk runs the week", "stages": ["B1"], "what": "Classes live on one schedule instead of a whiteboard."},
    {"name": "Members book themselves", "stages": ["B2", "B3"], "what": "The phone stops ringing for bookings."},
]

DECISIONS = [
    {"n": 1, "topic": "Capacity", "status": "agreed", "text": "A hard cap for members; the desk and owner may go over with a reason."},
    {"n": 2, "topic": "Clashes", "status": "agreed", "text": "A copied class that clashes is flagged, never moved automatically."},
    {"n": 3, "topic": "Cancel cut-off", "status": "agreed", "text": "Free to cancel until 12 h before the start. A later cancel still frees the place but counts as a No-show."},
    {"n": 4, "topic": "Reminder", "status": "assumed", "text": "One push 2 h before the start; no email in v1."},
    {"n": 5, "topic": "Waitlist offer", "status": "assumed", "text": "A freed place is held for the next person for 30 minutes."},
]

VOCABULARY = {
    "use": ["Class", "Class type", "Booking", "Place", "Waitlist", "Came", "No-show"],
    "never": {"session": "say 'class'", "slot": "say 'place'"},
}
