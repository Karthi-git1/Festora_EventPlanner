/**
 * FESTORA — AI-Powered Smart Personal Event Organizer
 * Complete Application Controller:
 * - Multi-Event Workspaces & Dynamic Event Creation Wizard
 * - Dynamic Category Planning tailored to event type (Wedding, Birthday, etc.)
 * - Asana-Style 2-Column Checklist & Dedicated Event AI Copilot
 * - Interactive Budget Planner with Over-Budget Alerts
 * - Chronological Event Timeline, Guest RSVP Management, & Vendor Directory
 * - Authentic 3D Page-Turning Keepsake Diary with 9 Illustrated Stationery Frames
 * - Perfectly Aligned 7-Column Monthly Calendar with Hover Details
 */

document.addEventListener('DOMContentLoaded', () => {
  const App = {
    // Multi-Event State
    events: [],
    activeEvent: null,
    activeTab: 'dashboard',
    currentWsPane: 'overview',
    activeTheme: "kitty-cozy",
    activeDiaryPattern: "pattern_kitty.png",
    calendarDate: new Date(2026, 10, 1), // November 2026 default
    selectedDateStr: null,
    selectedTaskId: null,
    currentDiaryPageIndex: 0,
    currentFilterCategory: 'all',

    // Category presets for Event Creation Wizard preview
    categoryPresets: {
      "Wedding": [
        "Venue and Hall Booking", "Food and Catering", "Decoration",
        "Photography and Videography", "Makeup and Hairstyling", "Wedding Outfits",
        "Invitations", "Entertainment", "Transportation", "Accommodation",
        "Return Gifts", "Other Expenses"
      ],
      "Birthday": [
        "Venue", "Birthday Cake", "Decorations", "Food and Snacks",
        "Photography", "Entertainment", "Return Gifts", "Invitations"
      ],
      "Anniversary": [
        "Venue & Romantic Dining", "Decorations & Floral", "Photography & Video",
        "Cake & Toast", "Attire & Styling", "Music & Entertainment", "Invitations & Gifts"
      ],
      "Corporate": [
        "Conference Venue & Hall", "AV Equipment & Tech", "Catering & Coffee Breaks",
        "Guest Speakers & Honorariums", "Badges & Welcome Kits", "Branding & Marketing", "Logistics & Transport"
      ],
      "Baby Shower": [
        "Venue", "Cradle & Floral Decor", "Traditional Catering & Sweets",
        "Photography & Portraits", "Mom-to-be Attire", "Return Favors"
      ],
      "Party": [
        "Venue & Space", "Food & Beverages", "Decor & Lighting",
        "Music & DJ", "Photography", "Party Favors"
      ],
      "Other": [
        "Venue Reservation", "Catering & Refreshments", "Decoration & Ambiance",
        "Invitations & RSVPs", "Photography & Video", "Music & Logistics"
      ]
    },

    async init() {
      this.bindElements();
      this.attachEvents();
      await this.loadInitialData();
      this.renderAll();
    },

    bindElements() {
      // Sidebar Navigation
      this.sidebar = document.getElementById('sidebar');
      this.sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
      this.mobileToggleBtn = document.getElementById('mobileToggleBtn');
      this.navItems = document.querySelectorAll('.nav-item');
      this.tabPanes = document.querySelectorAll('.tab-pane');
      this.currentSectionTitle = document.getElementById('currentSectionTitle');
      this.badgeTasksCount = document.getElementById('badgeTasksCount');
      this.badgeBudgetStatus = document.getElementById('badgeBudgetStatus');
      this.badgeGuestsCount = document.getElementById('badgeGuestsCount');
      this.badgeVendorsCount = document.getElementById('badgeVendorsCount');
      this.sidebarThemeName = document.getElementById('sidebarThemeName');
      this.sidebarDiaryBadge = document.getElementById('sidebarDiaryBadge');

      // Sidebar Celebrations & Actions
      this.sidebarNewEventBtn = document.getElementById('sidebarNewEventBtn');
      this.sidebarEventsList = document.getElementById('sidebarEventsList');
      this.sidebarEventsBadge = document.getElementById('sidebarEventsBadge');
      this.topbarEventHeading = document.getElementById('topbarEventHeading');
      this.emptyDashboardWelcome = document.getElementById('emptyDashboardWelcome');
      this.btnEdwCreate = document.getElementById('btnEdwCreate');
      this.btnEdwAi = document.getElementById('btnEdwAi');
      this.btnTopbarAskAi = document.getElementById('btnTopbarAskAi');
      this.eventHeroBanner = document.getElementById('eventHeroBanner');
      this.btnHeroDeleteEvent = document.getElementById('btnHeroDeleteEvent');

      // Topbar & Event Switcher
      this.topbarEventPill = document.getElementById('topbarEventPill');
      this.topbarEventIcon = document.getElementById('topbarEventIcon');
      this.topbarEventName = document.getElementById('topbarEventName');
      this.topbarEventCountdown = document.getElementById('topbarEventCountdown');
      this.eventSwitcherDropdown = document.getElementById('eventSwitcherDropdown');
      this.eventSwitcherList = document.getElementById('eventSwitcherList');
      this.btnOpenCreateEvent = document.getElementById('btnOpenCreateEvent');
      this.btnTopbarNewEvent = document.getElementById('btnTopbarNewEvent');
      this.btnTopbarAddTask = document.getElementById('btnTopbarAddTask');

      // Overview Hero & 4 Metric Cards
      this.heroEventType = document.getElementById('heroEventType');
      this.heroCountdownBadge = document.getElementById('heroCountdownBadge');
      this.heroEventTitle = document.getElementById('heroEventTitle');
      this.heroEventDate = document.getElementById('heroEventDate');
      this.heroEventLocation = document.getElementById('heroEventLocation');
      this.heroEventGuests = document.getElementById('heroEventGuests');
      this.heroEventDuration = document.getElementById('heroEventDuration');
      this.btnHeroSwitchEvent = document.getElementById('btnHeroSwitchEvent');
      this.btnHeroAddTask = document.getElementById('btnHeroAddTask');

      this.omcBudgetValue = document.getElementById('omcBudgetValue');
      this.omcBudgetSubtext = document.getElementById('omcBudgetSubtext');
      this.omcBudgetBar = document.getElementById('omcBudgetBar');
      this.omcTasksValue = document.getElementById('omcTasksValue');
      this.omcTasksSubtext = document.getElementById('omcTasksSubtext');
      this.omcTasksBar = document.getElementById('omcTasksBar');
      this.omcGuestsValue = document.getElementById('omcGuestsValue');
      this.omcGuestsSubtext = document.getElementById('omcGuestsSubtext');
      this.omcGuestsBar = document.getElementById('omcGuestsBar');
      this.omcVendorsValue = document.getElementById('omcVendorsValue');
      this.omcVendorsSubtext = document.getElementById('omcVendorsSubtext');
      this.omcVendorsBar = document.getElementById('omcVendorsBar');

      // Dashboard Calendar
      this.calMonthLabel = document.getElementById('calMonthLabel');
      this.calPrevMonth = document.getElementById('calPrevMonth');
      this.calNextMonth = document.getElementById('calNextMonth');
      this.calTodayBtn = document.getElementById('calTodayBtn');
      this.calendarDaysGrid = document.getElementById('calendarDaysGrid');
      this.calTotalPlansCount = document.getElementById('calTotalPlansCount');
      this.calendarTooltip = document.getElementById('calendarTooltip');
      this.cptDate = document.getElementById('cptDate');
      this.cptCountBadge = document.getElementById('cptCountBadge');
      this.cptItemsList = document.getElementById('cptItemsList');

      // Tasks & AI Copilot (Asana-Style)
      this.btnPaneAddTask = document.getElementById('btnPaneAddTask');
      this.taskViewFilter = document.getElementById('taskViewFilter');
      this.plannerSearchInput = document.getElementById('plannerSearchInput');
      this.plannerCatChipsContainer = document.getElementById('plannerCatChips');
      this.asanaTasksList = document.getElementById('asanaTasksList');
      this.aiConversationStream = document.getElementById('aiConversationStream');
      this.aiComposerInput = document.getElementById('aiComposerInput');
      this.btnSendAIComposer = document.getElementById('btnSendAIComposer');
      this.btnResetAIChat = document.getElementById('btnResetAIChat');
      this.aiChipActions = document.querySelectorAll('.ai-chip-action');

      // Budget Planner
      this.budgetTargetValue = document.getElementById('budgetTargetValue');
      this.budgetAllocatedValue = document.getElementById('budgetAllocatedValue');
      this.budgetSpentValue = document.getElementById('budgetSpentValue');
      this.budgetAllocatedTag = document.getElementById('budgetAllocatedTag');
      this.budgetRemainingTag = document.getElementById('budgetRemainingTag');
      this.budgetWarningAlert = document.getElementById('budgetWarningAlert');
      this.budgetWarningText = document.getElementById('budgetWarningText');
      this.budgetTableBody = document.getElementById('budgetTableBody');
      this.btnOpenAddBudget = document.getElementById('btnOpenAddBudget');

      // Timeline
      this.timelinePhasesList = document.getElementById('timelinePhasesList');
      this.btnOpenAddTimeline = document.getElementById('btnOpenAddTimeline');

      // Guests
      this.kpiGuestsTotal = document.getElementById('kpiGuestsTotal');
      this.kpiGuestsConfirmed = document.getElementById('kpiGuestsConfirmed');
      this.kpiGuestsPending = document.getElementById('kpiGuestsPending');
      this.kpiGuestsHeadcount = document.getElementById('kpiGuestsHeadcount');
      this.guestsTableBody = document.getElementById('guestsTableBody');
      this.btnOpenAddGuest = document.getElementById('btnOpenAddGuest');

      // Vendors
      this.kpiVendorsCount = document.getElementById('kpiVendorsCount');
      this.kpiVendorsQuoted = document.getElementById('kpiVendorsQuoted');
      this.kpiVendorsPaid = document.getElementById('kpiVendorsPaid');
      this.kpiVendorsBalance = document.getElementById('kpiVendorsBalance');
      this.vendorsTableBody = document.getElementById('vendorsTableBody');
      this.btnOpenAddVendor = document.getElementById('btnOpenAddVendor');

      // Notes
      this.notesCardsGrid = document.getElementById('notesCardsGrid');
      this.btnOpenAddNote = document.getElementById('btnOpenAddNote');

      // Keepsake Diary
      this.diaryBookSpread = document.getElementById('diaryBookSpread');
      this.diaryLeftPage = document.getElementById('diaryLeftPage');
      this.diaryRightPage = document.getElementById('diaryRightPage');
      this.bookChaptersList = document.getElementById('bookChaptersList');
      this.leftPageNumber = document.getElementById('leftPageNumber');
      this.rightPageNumber = document.getElementById('rightPageNumber');
      this.btnTurnNewPage = document.getElementById('btnTurnNewPage');
      this.diaryStationeryFrame = document.getElementById('diaryStationeryFrame');
      this.diaryInputDate = document.getElementById('diaryInputDate');
      this.diarySelectMood = document.getElementById('diarySelectMood');
      this.diaryInputTitle = document.getElementById('diaryInputTitle');
      this.diaryInputContent = document.getElementById('diaryInputContent');
      this.btnSaveDiaryEntry = document.getElementById('btnSaveDiaryEntry');
      this.btnPrevPage = document.getElementById('btnPrevPage');
      this.btnNextPage = document.getElementById('btnNextPage');
      this.bookPageIndicator = document.getElementById('bookPageIndicator');
      this.btnPrintDiary = document.getElementById('btnPrintDiary');
      this.patPills = document.querySelectorAll('.pat-pill');

      // Settings
      this.themeMoodCards = document.querySelectorAll('.theme-mood-card');
      this.activeThemeBadge = document.getElementById('activeThemeBadge');

      // Modals
      this.modalCreateEvent = document.getElementById('modalCreateEvent');
      this.formCreateEvent = document.getElementById('formCreateEvent');
      this.newEventType = document.getElementById('newEventType');
      this.catPreviewPills = document.getElementById('catPreviewPills');
      this.btnSubmitCreateEvent = document.getElementById('btnSubmitCreateEvent');

      this.modalAddTask = document.getElementById('modalAddTask');
      this.formTask = document.getElementById('formTask');
      this.taskIdHidden = document.getElementById('taskIdHidden');
      this.taskTitleInput = document.getElementById('taskTitleInput');
      this.taskDueDateInput = document.getElementById('taskDueDateInput');
      this.taskCategoryInput = document.getElementById('taskCategoryInput');
      this.taskNotesInput = document.getElementById('taskNotesInput');
      this.taskSelectedSymbol = document.getElementById('taskSelectedSymbol');
      this.btnSubmitTask = document.getElementById('btnSubmitTask');
      this.taskModalHeading = document.getElementById('taskModalHeading');

      this.modalAddBudget = document.getElementById('modalAddBudget');
      this.formBudget = document.getElementById('formBudget');
      this.budgetIdHidden = document.getElementById('budgetIdHidden');
      this.budgetCatInput = document.getElementById('budgetCatInput');
      this.budgetAllocInput = document.getElementById('budgetAllocInput');
      this.budgetSpentInput = document.getElementById('budgetSpentInput');
      this.budgetNotesInput = document.getElementById('budgetNotesInput');
      this.btnSubmitBudget = document.getElementById('btnSubmitBudget');

      this.modalAddGuest = document.getElementById('modalAddGuest');
      this.formGuest = document.getElementById('formGuest');
      this.guestIdHidden = document.getElementById('guestIdHidden');
      this.guestNameInput = document.getElementById('guestNameInput');
      this.guestPhoneInput = document.getElementById('guestPhoneInput');
      this.guestEmailInput = document.getElementById('guestEmailInput');
      this.guestRsvpInput = document.getElementById('guestRsvpInput');
      this.guestCountInput = document.getElementById('guestCountInput');
      this.guestCategoryInput = document.getElementById('guestCategoryInput');
      this.guestDietaryInput = document.getElementById('guestDietaryInput');
      this.btnSubmitGuest = document.getElementById('btnSubmitGuest');

      this.modalAddVendor = document.getElementById('modalAddVendor');
      this.formVendor = document.getElementById('formVendor');
      this.vendorIdHidden = document.getElementById('vendorIdHidden');
      this.vendorNameInput = document.getElementById('vendorNameInput');
      this.vendorCategoryInput = document.getElementById('vendorCategoryInput');
      this.vendorContactInput = document.getElementById('vendorContactInput');
      this.vendorQuotedInput = document.getElementById('vendorQuotedInput');
      this.vendorAdvanceInput = document.getElementById('vendorAdvanceInput');
      this.vendorStatusInput = document.getElementById('vendorStatusInput');
      this.vendorNotesInput = document.getElementById('vendorNotesInput');
      this.btnSubmitVendor = document.getElementById('btnSubmitVendor');

      this.modalAddTimeline = document.getElementById('modalAddTimeline');
      this.formTimeline = document.getElementById('formTimeline');
      this.timelineIdHidden = document.getElementById('timelineIdHidden');
      this.timelinePhaseInput = document.getElementById('timelinePhaseInput');
      this.timelineTitleInput = document.getElementById('timelineTitleInput');
      this.timelineDateInput = document.getElementById('timelineDateInput');
      this.btnSubmitTimeline = document.getElementById('btnSubmitTimeline');

      this.modalAddNote = document.getElementById('modalAddNote');
      this.formNote = document.getElementById('formNote');
      this.noteIdHidden = document.getElementById('noteIdHidden');
      this.noteTitleInput = document.getElementById('noteTitleInput');
      this.noteTagInput = document.getElementById('noteTagInput');
      this.noteContentInput = document.getElementById('noteContentInput');
      this.btnSubmitNote = document.getElementById('btnSubmitNote');

      // Workspace Subnav & Panes
      this.workspaceSubnavBar = document.getElementById('workspaceSubnavBar');
      this.wsSubnavPills = document.querySelectorAll('.ws-subnav-pill');
      this.wsPanes = document.querySelectorAll('.ws-pane');

      // Reminders Widget & Modal
      this.remindersPanel = document.getElementById('remindersPanel');
      this.remindersList = document.getElementById('remindersList');
      this.btnOpenAddReminder = document.getElementById('btnOpenAddReminder');
      this.modalAddReminder = document.getElementById('modalAddReminder');
      this.formReminder = document.getElementById('formReminder');
      this.reminderIdHidden = document.getElementById('reminderIdHidden');
      this.reminderTitleInput = document.getElementById('reminderTitleInput');
      this.reminderDateInput = document.getElementById('reminderDateInput');
      this.reminderTimeInput = document.getElementById('reminderTimeInput');
      this.reminderPriorityInput = document.getElementById('reminderPriorityInput');
      this.reminderNotesInput = document.getElementById('reminderNotesInput');
      this.btnSubmitReminder = document.getElementById('btnSubmitReminder');
      this.reminderModalHeading = document.getElementById('reminderModalHeading');

      // My Events Manager Hub
      this.eventsManagerGrid = document.getElementById('eventsManagerGrid');
      this.btnHubCreateEvent = document.getElementById('btnHubCreateEvent');
      this.badgeEventsCount = document.getElementById('badgeEventsCount');

      // Hero Edit Event & Modal
      this.btnHeroEditEvent = document.getElementById('btnHeroEditEvent');
      this.modalEditEvent = document.getElementById('modalEditEvent');
      this.formEditEvent = document.getElementById('formEditEvent');
      this.editEventIdHidden = document.getElementById('editEventIdHidden');
      this.editEventName = document.getElementById('editEventName');
      this.editEventType = document.getElementById('editEventType');
      this.editEventDate = document.getElementById('editEventDate');
      this.editEventLocation = document.getElementById('editEventLocation');
      this.editEventGuests = document.getElementById('editEventGuests');
      this.editEventCurrency = document.getElementById('editEventCurrency');
      this.editEventBudget = document.getElementById('editEventBudget');
      this.editEventDuration = document.getElementById('editEventDuration');
      this.editEventNotes = document.getElementById('editEventNotes');
      this.btnSubmitEditEvent = document.getElementById('btnSubmitEditEvent');

      // Dedicated AI Copilot
      this.dedicatedAiStream = document.getElementById('dedicatedAiStream');
      this.dedicatedAiInput = document.getElementById('dedicatedAiInput');
      this.btnDedicatedAiSend = document.getElementById('btnDedicatedAiSend');
      this.btnDedicatedAiReset = document.getElementById('btnDedicatedAiReset');
      this.copilotActiveEventName = document.getElementById('copilotActiveEventName');
      this.copilotActiveEventType = document.getElementById('copilotActiveEventType');
      this.copilotActiveLocation = document.getElementById('copilotActiveLocation');
      this.copilotActiveBudget = document.getElementById('copilotActiveBudget');
      this.copilotStreamEventName = document.getElementById('copilotStreamEventName');

      // Floating AI Copilot Drawer
      this.floatingAiBtn = document.getElementById('floatingAiBtn');
      this.floatingAiDrawer = document.getElementById('floatingAiDrawer');
      this.floatingAiBackdrop = document.getElementById('floatingAiBackdrop');
      this.btnCloseFloatingAi = document.getElementById('btnCloseFloatingAi');
      this.floatingAiContextBadge = document.getElementById('floatingAiContextBadge');
      this.floatingAiStream = document.getElementById('floatingAiStream');
      this.floatingAiInput = document.getElementById('floatingAiInput');
      this.btnSendFloatingAi = document.getElementById('btnSendFloatingAi');
    },

    attachEvents() {
      // Sidebar collapse & mobile toggle
      this.sidebarCollapseBtn?.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          this.sidebar.classList.remove('mobile-open');
        } else {
          this.sidebar.classList.toggle('collapsed');
        }
      });
      this.mobileToggleBtn?.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          this.sidebar.classList.toggle('mobile-open');
        } else {
          this.sidebar.classList.toggle('collapsed');
        }
      });

      // Tab navigation
      this.navItems.forEach(item => {
        item.addEventListener('click', (e) => {
          e.preventDefault();
          const tab = item.getAttribute('data-tab');
          this.switchTab(tab);
        });
      });

      document.getElementById('sidebarThemeTrigger')?.addEventListener('click', () => {
        this.switchTab('settings');
      });

      // Event Switcher dropdown toggle
      this.topbarEventPill?.addEventListener('click', (e) => {
        // Prevent toggle if clicking inside the dropdown items
        if (e.target.closest('#eventSwitcherDropdown')) return;
        this.eventSwitcherDropdown?.classList.toggle('show');
      });

      document.addEventListener('click', (e) => {
        if (!this.topbarEventPill?.contains(e.target)) {
          this.eventSwitcherDropdown?.classList.remove('show');
        }
      });

      // Global Accessibility Keybinding (WCAG 2.1 - Esc to close dialogs & popups)
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' || e.key === 'Esc') {
          document.querySelectorAll('.modal-backdrop.show').forEach(m => m.classList.remove('show'));
          this.eventSwitcherDropdown?.classList.remove('show');
          if (this.calendarTooltip) this.calendarTooltip.style.display = 'none';
        }
      });

      // Create Event modal triggers & Actions
      this.sidebarNewEventBtn?.addEventListener('click', () => this.openCreateEventModal());
      this.btnEdwCreate?.addEventListener('click', () => this.openCreateEventModal());
      this.btnEdwAi?.addEventListener('click', () => this.openFloatingAiDrawer());
      this.btnTopbarAskAi?.addEventListener('click', () => this.openFloatingAiDrawer());
      this.btnHeroDeleteEvent?.addEventListener('click', () => {
        if (this.activeEvent) this.handleDeleteEvent(this.activeEvent.id);
      });
      this.btnOpenCreateEvent?.addEventListener('click', () => {
        this.eventSwitcherDropdown?.classList.remove('show');
        this.openCreateEventModal();
      });
      this.btnTopbarNewEvent?.addEventListener('click', () => this.openCreateEventModal());
      this.btnHeroSwitchEvent?.addEventListener('click', () => {
        this.switchTab('events');
      });

      // Wizard Dynamic Category Preview
      this.newEventType?.addEventListener('change', () => this.updateCategoryPreview());

      // Calendar Navigation
      this.calPrevMonth?.addEventListener('click', () => {
        this.calendarDate.setMonth(this.calendarDate.getMonth() - 1);
        this.renderCalendar();
      });
      this.calNextMonth?.addEventListener('click', () => {
        this.calendarDate.setMonth(this.calendarDate.getMonth() + 1);
        this.renderCalendar();
      });
      this.calTodayBtn?.addEventListener('click', () => {
        this.calendarDate = new Date();
        this.renderCalendar();
      });

      // Tasks View & Search Filters
      this.taskViewFilter?.addEventListener('change', () => this.renderAsanaTasks());
      this.plannerSearchInput?.addEventListener('input', () => this.renderAsanaTasks());

      // Task Symbol Picker
      document.querySelectorAll('#taskSymbolPicker .symbol-pick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          document.querySelectorAll('#taskSymbolPicker .symbol-pick-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          if (this.taskSelectedSymbol) this.taskSelectedSymbol.value = btn.getAttribute('data-symbol');
        });
      });

      // Modals Open Triggers
      this.btnTopbarAddTask?.addEventListener('click', () => this.openTaskModal());
      this.btnPaneAddTask?.addEventListener('click', () => this.openTaskModal());
      this.btnHeroAddTask?.addEventListener('click', () => this.openTaskModal());
      this.btnHeroEditEvent?.addEventListener('click', () => this.openEditEventModal());
      this.btnHubCreateEvent?.addEventListener('click', () => this.openCreateEventModal());
      this.btnOpenAddReminder?.addEventListener('click', () => this.openAddReminderModal());
      this.btnOpenAddBudget?.addEventListener('click', () => this.openBudgetModal());
      this.btnOpenAddGuest?.addEventListener('click', () => this.openGuestModal());
      this.btnOpenAddVendor?.addEventListener('click', () => this.openVendorModal());
      this.btnOpenAddTimeline?.addEventListener('click', () => this.openTimelineModal());
      this.btnOpenAddNote?.addEventListener('click', () => this.openNoteModal());

      // Workspace Subnav Pills click
      this.wsSubnavPills?.forEach(pill => {
        pill.addEventListener('click', () => {
          const pane = pill.getAttribute('data-ws-pane');
          this.switchWsPane(pane);
        });
      });

      // Modal Form Submissions
      this.btnSubmitCreateEvent?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleCreateEvent();
      });
      this.btnSubmitEditEvent?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveEditEvent();
      });
      this.btnSubmitReminder?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveReminder();
      });
      this.btnSubmitTask?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveTask();
      });
      this.btnSubmitBudget?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveBudget();
      });
      this.btnSubmitGuest?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveGuest();
      });
      this.btnSubmitVendor?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveVendor();
      });
      this.btnSubmitTimeline?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveTimeline();
      });
      this.btnSubmitNote?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveNote();
      });

      // Floating AI Drawer triggers
      this.floatingAiBtn?.addEventListener('click', () => this.openFloatingAiDrawer());
      this.btnCloseFloatingAi?.addEventListener('click', () => this.closeFloatingAiDrawer());
      this.floatingAiBackdrop?.addEventListener('click', () => this.closeFloatingAiDrawer());
      this.btnSendFloatingAi?.addEventListener('click', () => this.handleSendFloatingAi());
      this.floatingAiInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSendFloatingAi();
        }
      });
      document.querySelectorAll('#floatingAiQuickChips .ai-chip-action')?.forEach(chip => {
        chip.addEventListener('click', () => {
          const prompt = chip.getAttribute('data-floating-prompt');
          if (prompt && this.floatingAiInput) {
            this.floatingAiInput.value = prompt;
            this.handleSendFloatingAi();
          }
        });
      });

      // Dedicated AI Copilot triggers
      this.btnDedicatedAiSend?.addEventListener('click', () => this.handleSendDedicatedAi());
      this.dedicatedAiInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSendDedicatedAi();
        }
      });
      this.btnDedicatedAiReset?.addEventListener('click', () => this.resetDedicatedAiStream());
      document.querySelectorAll('#tab-copilot .ai-chip-action')?.forEach(chip => {
        chip.addEventListener('click', () => {
          const prompt = chip.getAttribute('data-dedicated-prompt');
          if (prompt && this.dedicatedAiInput) {
            this.dedicatedAiInput.value = prompt;
            this.handleSendDedicatedAi();
          }
        });
      });

      // Modal Close Buttons
      document.querySelectorAll('[data-close-modal]').forEach(btn => {
        btn.addEventListener('click', () => {
          const mId = btn.getAttribute('data-close-modal');
          const m = document.getElementById(mId);
          if (m) this.closeModal(m);
        });
      });
      document.querySelectorAll('.modal-backdrop').forEach(modal => {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) this.closeModal(modal);
        });
      });

      // Dedicated Event AI Copilot
      this.btnSendAIComposer?.addEventListener('click', () => this.handleSendAIChat());
      this.aiComposerInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSendAIChat();
        }
      });
      this.btnResetAIChat?.addEventListener('click', () => this.resetAIChat());
      this.aiChipActions?.forEach(chip => {
        chip.addEventListener('click', () => {
          const prompt = chip.getAttribute('data-prompt');
          if (prompt && this.aiComposerInput) {
            this.aiComposerInput.value = prompt;
            this.handleSendAIChat();
          }
        });
      });

      // Diary Book Controls
      this.btnPrevPage?.addEventListener('click', () => this.turnDiaryPage(-1));
      this.btnNextPage?.addEventListener('click', () => this.turnDiaryPage(1));
      this.btnTurnNewPage?.addEventListener('click', () => this.turnToNewEntryPage());
      this.btnSaveDiaryEntry?.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSaveDiary();
      });
      this.btnPrintDiary?.addEventListener('click', () => window.print());

      // Stationery Pattern Frame Pills
      this.patPills?.forEach(pill => {
        pill.addEventListener('click', () => {
          const pat = pill.getAttribute('data-pattern');
          this.setDiaryPattern(pat);
        });
      });

      // Theme Mood Switcher
      this.themeMoodCards?.forEach(card => {
        const btn = card.querySelector('.btn-apply-theme');
        btn?.addEventListener('click', () => {
          const theme = card.getAttribute('data-theme');
          this.applyTheme(theme);
        });
      });
    },

    /* ==========================================================================
       DATA LOADING & INITIALIZATION
       ========================================================================== */
    async loadInitialData() {
      try {
        // Load settings
        const settingsRes = await fetch('/api/settings');
        if (settingsRes.ok) {
          const st = await settingsRes.json();
          if (st.theme) this.applyTheme(st.theme, false);
          if (st.pattern) this.setDiaryPattern(st.pattern, false);
        }
      } catch (e) {
        console.warn('Settings load error:', e);
      }

      try {
        // Load all events
        const res = await fetch('/api/events');
        if (res.ok) {
          const data = await res.json();
          const rawEvents = data.events || [];
          this.events = rawEvents.map(e => {
            if (!e.id && e._id) e.id = String(e._id);
            return e;
          }).filter(e => e && e.id && e.id !== 'undefined');
          const activeId = data.activeEventId;
          if (this.events.length > 0) {
            this.activeEvent = this.events.find(e => (e.id === activeId) || (e._id === activeId)) || this.events[0];
          } else {
            this.activeEvent = null;
          }
        }
      } catch (err) {
        console.error('Events load error:', err);
      }

      // If active event has a specific date, sync calendar month to it
      if (this.activeEvent && this.activeEvent.date) {
        const parts = this.activeEvent.date.split('-');
        if (parts.length >= 2) {
          this.calendarDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, 1);
        }
      }
    },

    renderAll() {
      this.renderEventSwitcher();
      this.renderSidebarEvents();
      this.renderMyEvents();

      // Gracefully handle 0 events
      if (!this.activeEvent || this.events.length === 0) {
        if (this.emptyDashboardWelcome) this.emptyDashboardWelcome.style.display = 'block';
        if (this.eventHeroBanner) this.eventHeroBanner.style.display = 'none';
        if (this.workspaceSubnavBar) this.workspaceSubnavBar.style.display = 'none';
        if (this.topbarEventHeading) this.topbarEventHeading.textContent = 'No Celebration Selected';
        if (this.badgeEventsCount) this.badgeEventsCount.textContent = '0';
        if (this.sidebarEventsBadge) this.sidebarEventsBadge.textContent = '0';
        this.updateCopilotContextBanner();
        return;
      }

      // Active event exists
      if (this.emptyDashboardWelcome) this.emptyDashboardWelcome.style.display = 'none';
      if (this.eventHeroBanner) this.eventHeroBanner.style.display = 'flex';
      if (this.workspaceSubnavBar) this.workspaceSubnavBar.style.display = 'flex';
      if (this.topbarEventHeading) this.topbarEventHeading.textContent = this.activeEvent.name;
      if (this.badgeEventsCount) this.badgeEventsCount.textContent = this.events.length;
      if (this.sidebarEventsBadge) this.sidebarEventsBadge.textContent = this.events.length;

      this.renderOverviewHero();
      this.renderOverviewStats();
      this.renderCalendar();
      this.renderReminders();
      this.renderAsanaTasks();
      this.renderBudget();
      this.renderTimeline();
      this.renderGuests();
      this.renderVendors();
      this.renderNotes();
      this.renderDiaryBookSpread();
      this.updateCopilotContextBanner();
    },

    /* ==========================================================================
       CHATGPT-STYLE SIDEBAR CELEBRATIONS
       ========================================================================== */
    renderSidebarEvents() {
      if (!this.sidebarEventsList) return;
      this.sidebarEventsList.innerHTML = '';

      if (this.sidebarEventsBadge) {
        this.sidebarEventsBadge.textContent = this.events.length;
      }

      if (this.events.length === 0) {
        this.sidebarEventsList.innerHTML = `
          <div class="sidebar-empty-events">
            <i class="fa-regular fa-calendar-plus" style="display:block; font-size:1.3rem; margin-bottom:6px; opacity:0.6;"></i>
            No celebrations yet.<br>Click "New Celebration" above to start!
          </div>
        `;
        return;
      }

      const typeSymbols = {
        'Wedding': '💍', 'Birthday': '🎂', 'Anniversary': '💖',
        'Baby Shower': '🍼', 'Corporate': '💼', 'Party': '🎉', 'Other': '✨'
      };

      this.events.forEach(ev => {
        const evId = ev.id || ev._id;
        if (!evId || evId === 'undefined') return;
        const isActive = this.activeEvent && (this.activeEvent.id === evId || this.activeEvent._id === evId);
        const item = document.createElement('div');
        item.className = `sidebar-event-item ${isActive ? 'active' : ''}`;
        item.setAttribute('data-event-id', evId);

        const sym = typeSymbols[ev.type] || '✨';
        const countdown = this.calculateDaysRemaining(ev.date);
        const curr = ev.currency || '₹';
        const budgetStr = (parseFloat(ev.budget) || 0).toLocaleString();

        item.innerHTML = `
          <div class="sei-left">
            <span class="sei-icon">${sym}</span>
            <div class="sei-details">
              <span class="sei-name" title="${this.escapeHtml(ev.name)}">${this.escapeHtml(ev.name)}</span>
              <span class="sei-sub">${countdown.text} • ${curr}${budgetStr}</span>
            </div>
          </div>
          <button class="sei-del-btn" title="Delete celebration" data-del-id="${evId}">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        `;

        item.addEventListener('click', (e) => {
          if (e.target.closest('.sei-del-btn')) return;
          this.switchEvent(evId);
        });

        const delBtn = item.querySelector('.sei-del-btn');
        delBtn?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.handleDeleteEvent(evId);
        });

        this.sidebarEventsList.appendChild(item);
      });
    },

    /* ==========================================================================
       EVENT SWITCHER & NAVIGATION
       ========================================================================== */
    renderEventSwitcher() {
      if (!this.activeEvent) {
        if (this.topbarEventHeading) this.topbarEventHeading.textContent = 'No Celebration Selected';
        return;
      }

      if (this.topbarEventHeading) this.topbarEventHeading.textContent = this.activeEvent.name;

      const typeSymbols = {
        'Wedding': '💍', 'Birthday': '🎂', 'Anniversary': '💖',
        'Baby Shower': '🍼', 'Corporate': '💼', 'Party': '🎉', 'Other': '✨'
      };
      const symbol = typeSymbols[this.activeEvent.type] || '💍';

      if (this.topbarEventIcon) this.topbarEventIcon.textContent = symbol;
      if (this.topbarEventName) this.topbarEventName.textContent = this.activeEvent.name;

      // Countdown
      const countdown = this.calculateDaysRemaining(this.activeEvent.date);
      if (this.topbarEventCountdown) {
        this.topbarEventCountdown.textContent = countdown.text;
      }

      // Render Dropdown items
      if (this.eventSwitcherList) {
        this.eventSwitcherList.innerHTML = '';
        this.events.forEach(ev => {
          const item = document.createElement('div');
          item.className = `es-item ${ev.id === this.activeEvent.id ? 'active' : ''}`;
          const evSym = typeSymbols[ev.type] || '✨';
          const evCurr = ev.currency || '₹';
          const evBudget = (parseFloat(ev.budget) || 0).toLocaleString();

          item.innerHTML = `
            <div class="es-item-left">
              <span style="font-size: 1.2rem;">${evSym}</span>
              <div style="min-width: 0;">
                <div class="es-item-name">${this.escapeHtml(ev.name)}</div>
                <div class="es-item-meta">${ev.date || 'TBD'} • ${evCurr}${evBudget}</div>
              </div>
            </div>
            ${ev.id === this.activeEvent.id ? '<i class="fa-solid fa-check es-item-check"></i>' : ''}
          `;

          item.addEventListener('click', () => {
            this.switchEvent(ev.id);
            this.eventSwitcherDropdown?.classList.remove('show');
          });
          this.eventSwitcherList.appendChild(item);
        });
      }
    },

    async switchActiveEvent(eventId) {
      return this.switchEvent(eventId);
    },

    async switchEvent(eventId) {
      const found = this.events.find(e => e.id === eventId);
      if (!found) return;

      this.activeEvent = found;
      try {
        await fetch('/api/events/active', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ eventId })
        });
      } catch (err) {}

      // Update calendar date to match event month
      if (this.activeEvent.date) {
        const parts = this.activeEvent.date.split('-');
        if (parts.length >= 2) {
          this.calendarDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, 1);
        }
      }

      this.currentFilterCategory = 'all';
      this.selectedTaskId = null;
      this.currentDiaryPageIndex = 0;

      this.showToast(`✨ Switched to "${this.activeEvent.name}"`, 'success');
      this.renderAll();
      this.resetAIChat();
    },

    openCreateEventModal() {
      if (this.newEventType) this.newEventType.value = 'Wedding';
      this.updateCategoryPreview();

      const today = new Date();
      const defaultDate = new Date(today.getFullYear(), today.getMonth() + 1, 15);
      const dateStr = defaultDate.toISOString().split('T')[0];
      const dateInput = document.getElementById('newEventDate');
      if (dateInput) dateInput.value = dateStr;

      this.openModal(this.modalCreateEvent);
    },

    updateCategoryPreview() {
      if (!this.catPreviewPills || !this.newEventType) return;
      const type = this.newEventType.value || 'Wedding';
      const cats = this.categoryPresets[type] || this.categoryPresets['Wedding'];

      this.catPreviewPills.innerHTML = '';
      cats.forEach(c => {
        const span = document.createElement('span');
        span.className = 'cat-preview-tag';
        span.textContent = c;
        this.catPreviewPills.appendChild(span);
      });
    },

    async handleCreateEvent() {
      const name = document.getElementById('newEventName')?.value.trim();
      const type = document.getElementById('newEventType')?.value;
      const date = document.getElementById('newEventDate')?.value;
      const location = document.getElementById('newEventLocation')?.value.trim();
      const guests = parseInt(document.getElementById('newEventGuests')?.value || '100');
      const currency = document.getElementById('newEventCurrency')?.value || '₹';
      const budget = parseFloat(document.getElementById('newEventBudget')?.value || '200000');
      const duration = document.getElementById('newEventDuration')?.value || '1 Day';
      const notes = document.getElementById('newEventNotes')?.value.trim();

      if (!name) {
        this.showToast('Please enter an event name.', 'error');
        return;
      }

      const payload = {
        name, type, date, location, guests, currency, budget, duration, notes,
        categories: this.categoryPresets[type] || this.categoryPresets['Wedding']
      };

      try {
        const res = await fetch('/api/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          const newEv = data.event;
          this.events.unshift(newEv);
          this.activeEvent = newEv;
          this.closeModal(this.modalCreateEvent);
          this.showToast(`🎉 Dedicated workspace for "${newEv.name}" created!`, 'success');
          this.renderAll();
          this.resetAIChat();
        } else {
          this.showToast('Could not create event.', 'error');
        }
      } catch (err) {
        console.error('Create event error:', err);
        this.showToast('Error connecting to server.', 'error');
      }
    },

    /* ==========================================================================
       DASHBOARD OVERVIEW HERO & 4 STAT METRICS CARDS
       ========================================================================== */
    renderOverviewHero() {
      if (!this.activeEvent) return;

      const ev = this.activeEvent;
      if (this.heroEventType) this.heroEventType.textContent = ev.type || 'Celebration';

      const countdown = this.calculateDaysRemaining(ev.date);
      if (this.heroCountdownBadge) {
        this.heroCountdownBadge.textContent = countdown.text;
      }

      if (this.heroEventTitle) this.heroEventTitle.textContent = ev.name;
      if (this.heroEventDate) {
        const d = ev.date ? new Date(ev.date + 'T00:00:00') : new Date();
        this.heroEventDate.textContent = d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
      }
      if (this.heroEventLocation) this.heroEventLocation.textContent = ev.location || 'Location Pending';
      if (this.heroEventGuests) this.heroEventGuests.textContent = `${ev.guests || 0} Guests`;
      if (this.heroEventDuration) this.heroEventDuration.textContent = `${ev.duration || '1 Day'} Event`;
    },

    renderOverviewStats() {
      if (!this.activeEvent) return;

      const ev = this.activeEvent;
      const currency = ev.currency || '₹';
      const totalBudget = parseFloat(ev.budget) || 0;
      const budgetItems = ev.budgetItems || [];
      const totalSpent = budgetItems.reduce((acc, b) => acc + (parseFloat(b.spent) || 0), 0);
      const remaining = totalBudget - totalSpent;

      // Card 1: Budget
      if (this.omcBudgetValue) {
        this.omcBudgetValue.textContent = `${currency}${totalBudget.toLocaleString()}`;
      }
      if (this.omcBudgetSubtext) {
        this.omcBudgetSubtext.textContent = `${currency}${totalSpent.toLocaleString()} spent • ${currency}${Math.max(0, remaining).toLocaleString()} buffer remaining`;
      }
      if (this.omcBudgetBar) {
        const pct = totalBudget > 0 ? Math.min(100, Math.round((totalSpent / totalBudget) * 100)) : 0;
        this.omcBudgetBar.style.width = `${pct}%`;
        this.omcBudgetBar.style.background = remaining < 0 ? '#DC3545' : 'var(--color-primary)';
      }
      if (this.badgeBudgetStatus) {
        this.badgeBudgetStatus.textContent = `${currency}${totalSpent.toLocaleString()}`;
      }

      // Card 2: Tasks Checklist
      const tasks = ev.tasks || [];
      const completedTasks = tasks.filter(t => t.status === 'completed');
      const taskPct = tasks.length > 0 ? Math.round((completedTasks.length / tasks.length) * 100) : 0;

      if (this.omcTasksValue) {
        this.omcTasksValue.textContent = `${completedTasks.length} / ${tasks.length} Done`;
      }
      if (this.omcTasksSubtext) {
        const pendingCount = tasks.length - completedTasks.length;
        this.omcTasksSubtext.textContent = `${pendingCount} milestone${pendingCount === 1 ? '' : 's'} pending • ${taskPct}% complete`;
      }
      if (this.omcTasksBar) {
        this.omcTasksBar.style.width = `${taskPct}%`;
      }
      if (this.badgeTasksCount) {
        this.badgeTasksCount.textContent = tasks.length;
      }

      // Card 3: Guests
      const guests = ev.guestsList || [];
      const confirmedGuests = guests.filter(g => g.rsvp === 'Confirmed');
      const totalHeadcount = confirmedGuests.reduce((acc, g) => acc + (parseInt(g.attendeesCount) || 1), 0);

      const targetGuests = ev.guests || totalHeadcount || 300;

      if (this.omcGuestsValue) {
        this.omcGuestsValue.textContent = `${targetGuests} Guests`;
      }
      if (this.omcGuestsSubtext) {
        this.omcGuestsSubtext.textContent = `${totalHeadcount} RSVPs Confirmed • Target ${targetGuests} Headcount`;
      }
      if (this.omcGuestsBar) {
        const gPct = Math.min(100, Math.round((totalHeadcount / targetGuests) * 100));
        this.omcGuestsBar.style.width = `${gPct}%`;
      }
      if (this.badgeGuestsCount) {
        this.badgeGuestsCount.textContent = guests.length;
      }

      // Card 4: Vendors
      const vendors = ev.vendors || [];
      const bookedVendors = vendors.filter(v => v.status === 'Booked' || v.status === 'Completed');

      if (this.omcVendorsValue) {
        this.omcVendorsValue.textContent = `${bookedVendors.length} / ${vendors.length} Booked`;
      }
      if (this.omcVendorsSubtext) {
        this.omcVendorsSubtext.textContent = `${vendors.length - bookedVendors.length} in negotiation • ${bookedVendors.length} confirmed partners`;
      }
      if (this.omcVendorsBar) {
        const vPct = vendors.length > 0 ? Math.min(100, Math.round((bookedVendors.length / vendors.length) * 100)) : 0;
        this.omcVendorsBar.style.width = `${vPct}%`;
      }
      if (this.badgeVendorsCount) {
        this.badgeVendorsCount.textContent = vendors.length;
      }
    },

    calculateDaysRemaining(dateStr) {
      if (!dateStr) return { days: 0, text: 'Date TBD' };
      const eventDate = new Date(dateStr + 'T00:00:00');
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const diffTime = eventDate.getTime() - today.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays < 0) return { days: diffDays, text: 'Celebration Concluded 🎉' };
      if (diffDays === 0) return { days: 0, text: 'Happening Today! 🌟' };
      if (diffDays === 1) return { days: 1, text: '⏳ Tomorrow!' };
      return { days: diffDays, text: `⏳ ${diffDays} Days to go` };
    },

    /* ==========================================================================
       PERFECTLY ALIGNED MONTHLY CALENDAR GRID
       ========================================================================== */
    renderCalendar() {
      if (!this.calendarDaysGrid || !this.activeEvent) return;
      this.calendarDaysGrid.innerHTML = '';

      const year = this.calendarDate.getFullYear();
      const month = this.calendarDate.getMonth();
      const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      if (this.calMonthLabel) {
        this.calMonthLabel.textContent = `${monthNames[month]} ${year}`;
      }

      const firstDayIndex = new Date(year, month, 1).getDay();
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      const prevMonthDays = new Date(year, month, 0).getDate();

      const today = new Date();
      const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

      let currentMonthPlanCount = 0;

      // Trailing previous month days
      for (let i = firstDayIndex - 1; i >= 0; i--) {
        const d = prevMonthDays - i;
        const prevMonth = month === 0 ? 11 : month - 1;
        const prevYear = month === 0 ? year - 1 : year;
        const dateStr = `${prevYear}-${String(prevMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const tile = this.createCalendarTile(d, dateStr, true, dateStr === todayStr);
        this.calendarDaysGrid.appendChild(tile);
      }

      // Current month days
      for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const dayTasks = this.getTasksForDate(dateStr);
        if (dayTasks.length > 0) currentMonthPlanCount += dayTasks.length;
        const tile = this.createCalendarTile(d, dateStr, false, dateStr === todayStr);
        this.calendarDaysGrid.appendChild(tile);
      }

      // Next month trailing days
      const totalTiles = firstDayIndex + daysInMonth;
      const remainingTiles = totalTiles <= 35 ? 35 - totalTiles : 42 - totalTiles;
      for (let d = 1; d <= remainingTiles; d++) {
        const nextMonth = month === 11 ? 0 : month + 1;
        const nextYear = month === 11 ? year + 1 : year;
        const dateStr = `${nextYear}-${String(nextMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const tile = this.createCalendarTile(d, dateStr, true, dateStr === todayStr);
        this.calendarDaysGrid.appendChild(tile);
      }

      if (this.calTotalPlansCount) {
        this.calTotalPlansCount.textContent = `${currentMonthPlanCount} plan${currentMonthPlanCount === 1 ? '' : 's'} scheduled`;
      }
    },

    getTasksForDate(dateStr) {
      if (!this.activeEvent) return [];
      const tasks = this.activeEvent.tasks || [];
      return tasks.filter(t => (t.dueDate === dateStr || t.date === dateStr));
    },

    createCalendarTile(dayNum, dateStr, isOtherMonth, isToday) {
      const tile = document.createElement('div');
      tile.className = `cal-day-tile ${isOtherMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`;
      if (this.selectedDateStr === dateStr) tile.classList.add('selected');

      const isEventDay = (this.activeEvent && this.activeEvent.date === dateStr);
      if (isEventDay) tile.style.borderColor = 'var(--color-primary)';

      const dayTasks = this.getTasksForDate(dateStr);

      const topRow = document.createElement('div');
      topRow.className = 'tile-top-row';
      const numSpan = document.createElement('span');
      numSpan.className = 'tile-day-num';
      numSpan.textContent = dayNum;
      topRow.appendChild(numSpan);

      if (isEventDay) {
        const evPill = document.createElement('span');
        evPill.className = 'tile-today-pill';
        evPill.style.background = 'var(--color-primary)';
        evPill.style.color = '#FFFFFF';
        evPill.textContent = 'Big Day! 💍';
        topRow.appendChild(evPill);
      } else if (isToday) {
        const todayPill = document.createElement('span');
        todayPill.className = 'tile-today-pill';
        todayPill.textContent = 'Today';
        topRow.appendChild(todayPill);
      }
      tile.appendChild(topRow);

      // Plan indicators
      const planWrap = document.createElement('div');
      planWrap.className = 'tile-plan-indicators';

      if (dayTasks.length > 0) {
        const dotsRow = document.createElement('div');
        dotsRow.className = 'tile-dots-row';

        const maxDots = Math.min(dayTasks.length, 3);
        for (let i = 0; i < maxDots; i++) {
          const dot = document.createElement('span');
          dot.className = 'cal-dot';
          dotsRow.appendChild(dot);
        }
        planWrap.appendChild(dotsRow);

        const firstTask = dayTasks[0];
        const previewChip = document.createElement('div');
        previewChip.className = 'tile-chip-item';
        previewChip.innerHTML = `<span>${firstTask.symbol || '💍'}</span> <span>${this.escapeHtml(firstTask.title)}</span>`;
        planWrap.appendChild(previewChip);

        if (dayTasks.length > 1) {
          const moreEl = document.createElement('div');
          moreEl.style.fontSize = '0.68rem';
          moreEl.style.color = 'var(--text-muted)';
          moreEl.style.fontWeight = '700';
          moreEl.textContent = `+${dayTasks.length - 1} more`;
          planWrap.appendChild(moreEl);
        }
      }
      tile.appendChild(planWrap);

      // Hover Tooltip Popover
      tile.addEventListener('mouseenter', (e) => {
        if (dayTasks.length > 0 || isEventDay) this.showCalendarTooltip(e, dateStr, dayTasks, isEventDay);
      });
      tile.addEventListener('mousemove', (e) => {
        if (dayTasks.length > 0 || isEventDay) this.positionCalendarTooltip(e);
      });
      tile.addEventListener('mouseleave', () => this.hideCalendarTooltip());

      // Click date to add task
      tile.addEventListener('click', () => {
        this.selectedDateStr = dateStr;
        document.querySelectorAll('.cal-day-tile').forEach(t => t.classList.remove('selected'));
        tile.classList.add('selected');
        this.openTaskModal(null, dateStr);
      });

      return tile;
    },

    showCalendarTooltip(e, dateStr, tasks, isEventDay) {
      if (!this.calendarTooltip) return;
      const d = new Date(dateStr + 'T00:00:00');
      const formatted = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

      if (this.cptDate) this.cptDate.textContent = formatted;
      if (this.cptCountBadge) {
        this.cptCountBadge.textContent = isEventDay ? 'Main Event Day' : `${tasks.length} plan${tasks.length === 1 ? '' : 's'}`;
      }

      if (this.cptItemsList) {
        this.cptItemsList.innerHTML = '';
        if (isEventDay) {
          const evItem = document.createElement('div');
          evItem.className = 'cpt-item';
          evItem.style.background = 'rgba(140, 83, 62, 0.08)';
          evItem.innerHTML = `
            <span style="font-size: 1.1rem;">🌟</span>
            <div class="cpt-item-info">
              <span class="cpt-item-title" style="font-weight: 800; color: var(--color-primary);">${this.escapeHtml(this.activeEvent.name)}</span>
              <span class="cpt-item-meta">${this.escapeHtml(this.activeEvent.type)} • ${this.escapeHtml(this.activeEvent.location || '')}</span>
            </div>
          `;
          this.cptItemsList.appendChild(evItem);
        }

        tasks.forEach(t => {
          const item = document.createElement('div');
          item.className = 'cpt-item';
          item.innerHTML = `
            <span style="font-size: 1rem;">${t.symbol || '💍'}</span>
            <div class="cpt-item-info">
              <span class="cpt-item-title">${this.escapeHtml(t.title)}</span>
              <span class="cpt-item-meta">${this.escapeHtml(t.category || 'General')} ${t.priority ? '• ' + t.priority.toUpperCase() : ''}</span>
            </div>
          `;
          this.cptItemsList.appendChild(item);
        });
      }

      this.calendarTooltip.style.display = 'block';
      this.positionCalendarTooltip(e);
    },

    positionCalendarTooltip(e) {
      if (!this.calendarTooltip) return;
      const offset = 14;
      let x = e.clientX + offset;
      let y = e.clientY + offset;

      const w = 300;
      const h = this.calendarTooltip.offsetHeight || 160;

      if (x + w > window.innerWidth) x = e.clientX - w - offset;
      if (y + h > window.innerHeight) y = e.clientY - h - offset;

      this.calendarTooltip.style.left = `${Math.max(10, x)}px`;
      this.calendarTooltip.style.top = `${Math.max(10, y)}px`;
    },

    hideCalendarTooltip() {
      if (this.calendarTooltip) this.calendarTooltip.style.display = 'none';
    },

    /* ==========================================================================
       TASKS & DEDICATED AI COPILOT (ASANA 2-COLUMN)
       ========================================================================== */
    renderAsanaTasks() {
      if (!this.asanaTasksList || !this.activeEvent) return;

      this.renderCategoryChips();

      let tasks = this.activeEvent.tasks || [];
      const viewMode = this.taskViewFilter ? this.taskViewFilter.value : 'incomplete';
      const search = this.plannerSearchInput ? this.plannerSearchInput.value.toLowerCase().trim() : '';

      // Filter by status
      if (viewMode === 'incomplete') {
        tasks = tasks.filter(t => t.status !== 'completed');
      } else if (viewMode === 'completed') {
        tasks = tasks.filter(t => t.status === 'completed');
      }

      // Filter by dynamic category
      if (this.currentFilterCategory && this.currentFilterCategory !== 'all') {
        tasks = tasks.filter(t => t.category === this.currentFilterCategory);
      }

      // Filter by search query
      if (search) {
        tasks = tasks.filter(t =>
          (t.title && t.title.toLowerCase().includes(search)) ||
          (t.category && t.category.toLowerCase().includes(search)) ||
          (t.notes && t.notes.toLowerCase().includes(search))
        );
      }

      this.asanaTasksList.innerHTML = '';
      if (tasks.length === 0) {
        this.asanaTasksList.innerHTML = `
          <div class="asana-empty-state">
            <i class="fa-solid fa-clipboard-check"></i>
            <h4>No tasks found</h4>
            <p>You're all caught up, or no tasks match your filter. Click "+ Add Task" or ask Festora AI on the right!</p>
          </div>
        `;
        return;
      }

      tasks.forEach(t => {
        const isDone = t.status === 'completed';
        const isSelected = this.selectedTaskId === t.id;
        const row = document.createElement('div');
        row.className = `asana-task-row ${isDone ? 'completed' : ''} ${isSelected ? 'selected' : ''}`;
        row.setAttribute('data-task-id', t.id);

        const prio = (t.priority || 'medium').toLowerCase();
        const prioBadge = `<span class="priority-flag ${prio}"><i class="fa-solid fa-flag"></i> ${prio.toUpperCase()}</span>`;

        row.innerHTML = `
          <div class="task-checkbox-wrap">
            <input type="checkbox" class="task-checkbox" ${isDone ? 'checked' : ''} title="Mark milestone complete">
          </div>
          <div class="task-main-info">
            <span class="task-symbol-badge">${t.symbol || '💍'}</span>
            <div class="task-title-group">
              <span class="task-title-text">${this.escapeHtml(t.title)}</span>
              ${t.notes ? `<span class="task-notes-snippet">${this.escapeHtml(t.notes)}</span>` : ''}
            </div>
          </div>
          <div class="task-meta-right">
            ${prioBadge}
            <span class="task-cat-pill">${this.escapeHtml(t.category || 'General')}</span>
            <span class="task-due-text ${this.isPastDue(t.dueDate) && !isDone ? 'overdue' : ''}">
              <i class="fa-regular fa-calendar"></i> ${t.dueDate || 'No Date'}
            </span>
            <div class="task-actions-hover">
              <button class="btn-task-action btn-edit-task" title="Edit Milestone"><i class="fa-solid fa-pen"></i></button>
              <button class="btn-task-action btn-delete-task" title="Remove Milestone"><i class="fa-solid fa-trash-can"></i></button>
            </div>
          </div>
        `;

        // Toggle checkbox
        const chk = row.querySelector('.task-checkbox');
        chk?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.toggleTaskStatus(t.id);
        });

        // Edit button
        row.querySelector('.btn-edit-task')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.openTaskModal(t);
        });

        // Delete button
        row.querySelector('.btn-delete-task')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.deleteTask(t.id);
        });

        // Row click to select & prompt AI
        row.addEventListener('click', () => {
          this.selectedTaskId = t.id;
          document.querySelectorAll('.asana-task-row').forEach(r => r.classList.remove('selected'));
          row.classList.add('selected');
        });

        this.asanaTasksList.appendChild(row);
      });
    },

    renderCategoryChips() {
      if (!this.plannerCatChipsContainer || !this.activeEvent) return;
      const categories = ['all', ...(this.activeEvent.categories || [])];

      this.plannerCatChipsContainer.innerHTML = '';
      categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = `cat-chip ${this.currentFilterCategory === cat ? 'active' : ''}`;
        btn.textContent = cat === 'all' ? 'All' : cat;
        btn.addEventListener('click', () => {
          this.currentFilterCategory = cat;
          this.renderAsanaTasks();
        });
        this.plannerCatChipsContainer.appendChild(btn);
      });
    },

    isPastDue(dateStr) {
      if (!dateStr) return false;
      const due = new Date(dateStr + 'T23:59:59');
      return due < new Date();
    },

    openTaskModal(task = null, presetDate = null) {
      if (!this.activeEvent) return;

      // Populate Category dropdown dynamically from active event
      if (this.taskCategoryInput) {
        this.taskCategoryInput.innerHTML = '';
        const cats = this.activeEvent.categories || ['General'];
        cats.forEach(c => {
          const opt = document.createElement('option');
          opt.value = c;
          opt.textContent = c;
          this.taskCategoryInput.appendChild(opt);
        });
      }

      if (task) {
        if (this.taskModalHeading) this.taskModalHeading.textContent = 'Edit Milestone';
        if (this.taskIdHidden) this.taskIdHidden.value = task.id;
        if (this.taskTitleInput) this.taskTitleInput.value = task.title || '';
        if (this.taskDueDateInput) this.taskDueDateInput.value = task.dueDate || task.date || '';
        if (this.taskCategoryInput) this.taskCategoryInput.value = task.category || '';
        if (this.taskNotesInput) this.taskNotesInput.value = task.notes || '';
        if (this.taskSelectedSymbol) this.taskSelectedSymbol.value = task.symbol || '💍';
      } else {
        if (this.taskModalHeading) this.taskModalHeading.textContent = 'Add Milestone to Checklist';
        if (this.taskIdHidden) this.taskIdHidden.value = '';
        if (this.taskTitleInput) this.taskTitleInput.value = '';
        if (this.taskDueDateInput) this.taskDueDateInput.value = presetDate || this.activeEvent.date || new Date().toISOString().split('T')[0];
        if (this.taskNotesInput) this.taskNotesInput.value = '';
        if (this.taskSelectedSymbol) this.taskSelectedSymbol.value = '💍';
      }

      // Highlight symbol button
      const sym = this.taskSelectedSymbol ? this.taskSelectedSymbol.value : '💍';
      document.querySelectorAll('#taskSymbolPicker .symbol-pick-btn').forEach(btn => {
        if (btn.getAttribute('data-symbol') === sym) btn.classList.add('active');
        else btn.classList.remove('active');
      });

      this.openModal(this.modalAddTask);
    },

    async handleSaveTask() {
      if (!this.activeEvent) return;

      const title = this.taskTitleInput?.value.trim();
      const dueDate = this.taskDueDateInput?.value;
      const category = this.taskCategoryInput?.value || 'General';
      const notes = this.taskNotesInput?.value.trim();
      const symbol = this.taskSelectedSymbol?.value || '💍';
      const id = this.taskIdHidden?.value || null;

      if (!title) {
        this.showToast('Please enter a milestone title.', 'error');
        return;
      }

      const taskData = { id, title, dueDate, category, notes, symbol, status: 'todo', priority: 'medium' };

      try {
        const url = `/api/events/${this.activeEvent.id}/tasks`;
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(taskData)
        });

        if (res.ok) {
          const data = await res.json();
          // Update in local memory
          if (!this.activeEvent.tasks) this.activeEvent.tasks = [];
          const idx = this.activeEvent.tasks.findIndex(t => t.id === data.task.id);
          if (idx >= 0) this.activeEvent.tasks[idx] = data.task;
          else this.activeEvent.tasks.unshift(data.task);

          this.closeModal(this.modalAddTask);
          this.showToast('✨ Milestone saved to your checklist!', 'success');
          this.renderOverviewStats();
          this.renderAsanaTasks();
          this.renderCalendar();
        }
      } catch (err) {
        this.showToast('Could not save milestone.', 'error');
      }
    },

    async deleteTask(taskId) {
      if (!this.activeEvent) return;
      if (!confirm('Remove this celebration milestone?')) return;

      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/tasks/${taskId}`, { method: 'DELETE' });
        if (res.ok) {
          this.activeEvent.tasks = (this.activeEvent.tasks || []).filter(t => t.id !== taskId);
          this.showToast('Milestone removed', 'info');
          this.renderOverviewStats();
          this.renderAsanaTasks();
          this.renderCalendar();
        }
      } catch (err) {}
    },

    async toggleTaskStatus(taskId) {
      if (!this.activeEvent) return;
      const task = (this.activeEvent.tasks || []).find(t => t.id === taskId);
      if (!task) return;

      task.status = (task.status === 'completed') ? 'todo' : 'completed';
      try {
        await fetch(`/api/events/${this.activeEvent.id}/tasks/${taskId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(task)
        });
        this.showToast(task.status === 'completed' ? '🎉 Milestone completed!' : 'Marked as to-do', 'success');
        this.renderOverviewStats();
        this.renderAsanaTasks();
        this.renderCalendar();
      } catch (err) {}
    },

    /* ==========================================================================
       EVENT-AWARE AI COPILOT, WEB RESEARCH & COST ESTIMATION
       ========================================================================== */
    handleSendAIChat() {
      if (!this.aiComposerInput || !this.aiConversationStream) return;
      const msg = this.aiComposerInput.value.trim();
      if (!msg) return;
      this.executeAiQuery(msg, this.aiConversationStream, this.aiComposerInput);
    },

    handleSendDedicatedAi() {
      if (!this.dedicatedAiInput || !this.dedicatedAiStream) return;
      const msg = this.dedicatedAiInput.value.trim();
      if (!msg) return;
      this.executeAiQuery(msg, this.dedicatedAiStream, this.dedicatedAiInput);
    },

    handleSendFloatingAi() {
      if (!this.floatingAiInput || !this.floatingAiStream) return;
      const msg = this.floatingAiInput.value.trim();
      if (!msg) return;
      this.executeAiQuery(msg, this.floatingAiStream, this.floatingAiInput);
    },

    openFloatingAiDrawer() {
      if (this.floatingAiDrawer) this.floatingAiDrawer.classList.add('open');
      if (this.floatingAiBackdrop) this.floatingAiBackdrop.classList.add('show');
      if (this.floatingAiInput) this.floatingAiInput.focus();
    },

    closeFloatingAiDrawer() {
      if (this.floatingAiDrawer) this.floatingAiDrawer.classList.remove('open');
      if (this.floatingAiBackdrop) this.floatingAiBackdrop.classList.remove('show');
    },

    resetDedicatedAiStream() {
      if (!this.dedicatedAiStream) return;
      const evName = this.activeEvent ? `<em>${this.escapeHtml(this.activeEvent.name)}</em>` : 'your celebrations';
      this.dedicatedAiStream.innerHTML = `
        <div class="ai-chat-item ai-response">
          <div class="chat-avatar-mini"><i class="fa-solid fa-wand-magic-sparkles"></i></div>
          <div class="chat-text">
            <p><strong>Festora AI Copilot Ready</strong></p>
            <p>I have context on ${evName}. Ask me to suggest ideas, recommend venues, estimate costs, adjust budgets, or add tasks to your checklist!</p>
          </div>
        </div>
      `;
    },

    resetAIChat() {
      if (!this.aiConversationStream) return;
      const evName = this.activeEvent ? `<em>${this.escapeHtml(this.activeEvent.name)}</em>` : 'your celebration';
      this.aiConversationStream.innerHTML = `
        <div class="ai-chat-item ai-response">
          <div class="chat-avatar-mini"><i class="fa-solid fa-wand-magic-sparkles"></i></div>
          <div class="chat-text">
            <p><strong>Hi! I am your AI Celebration Copilot.</strong></p>
            <p>I can customize your plans for ${evName} in real-time. Try typing: <em>"Suggest decor ideas"</em>, <em>"Add 3 catering tasks"</em>, or <em>"Reduce budget by 50,000"</em>!</p>
          </div>
        </div>
      `;
    },

    async executeAiQuery(userMessage, streamContainer, inputEl = null) {
      if (!userMessage || !streamContainer) return;
      if (inputEl) inputEl.value = '';

      // Append user bubble
      const userBubble = document.createElement('div');
      userBubble.className = 'ai-chat-item ai-user user-msg';
      userBubble.innerHTML = `
        <div class="chat-avatar-mini"><i class="fa-solid fa-user"></i></div>
        <div class="chat-text"><p>${this.escapeHtml(userMessage)}</p></div>
      `;
      streamContainer.appendChild(userBubble);
      streamContainer.scrollTop = streamContainer.scrollHeight;

      // Loading bubble
      const loadingBubble = document.createElement('div');
      loadingBubble.className = 'ai-chat-item ai-response';
      loadingBubble.innerHTML = `
        <div class="chat-avatar-mini"><i class="fa-solid fa-wand-magic-sparkles"></i></div>
        <div class="chat-text"><p><i class="fa-solid fa-spinner fa-spin"></i> Researching and organizing...</p></div>
      `;
      streamContainer.appendChild(loadingBubble);
      streamContainer.scrollTop = streamContainer.scrollHeight;

      try {
        const eventId = this.activeEvent ? this.activeEvent.id : 'default';
        const res = await fetch(`/api/events/${eventId}/ai/copilot`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            current_section: this.currentWsPane || 'dashboard'
          })
        });

        if (res.ok) {
          const data = await res.json();
          loadingBubble.remove();

          if (data.event) {
            this.activeEvent = data.event;
            const idx = this.events.findIndex(e => e.id === data.event.id);
            if (idx >= 0) this.events[idx] = data.event;
            else this.events.unshift(data.event);
          }

          const responseBubble = document.createElement('div');
          responseBubble.className = 'ai-chat-item ai-response';

          let contentHtml = this.formatMarkdown(data.reply || '');

          // 1. Action Executed Confirmation Card
          if (data.executed_action) {
            const act = data.executed_action;
            if (act.type === 'task_added') {
              contentHtml += `
                <div style="margin-top: 10px; padding: 8px 14px; border-radius: 8px; background: rgba(40, 167, 69, 0.12); color: #28A745; font-size: 0.82rem; font-weight: 700;">
                  <i class="fa-solid fa-circle-check"></i> Added "${this.escapeHtml(act.task?.title || 'Task')}" to your Checklist!
                </div>
              `;
            } else if (act.type === 'total_budget_updated') {
              const curr = this.activeEvent?.currency || '₹';
              const isRed = act.isReduction;
              const verb = isRed ? 'Reduced' : 'Increased';
              const icon = isRed ? 'fa-circle-minus' : 'fa-circle-check';
              contentHtml += `
                <div style="margin-top: 10px; padding: 8px 14px; border-radius: 8px; background: rgba(40, 167, 69, 0.12); color: #28A745; font-size: 0.82rem; font-weight: 700;">
                  <i class="fa-solid ${icon}"></i> ${verb} Total Event Budget to ${curr}${(parseFloat(act.newBudget || this.activeEvent?.budget || 0)).toLocaleString()}!
                </div>
              `;
            } else if (act.type === 'task_and_budget_added') {
              const curr = this.activeEvent?.currency || '₹';
              contentHtml += `
                <div style="margin-top: 10px; padding: 8px 14px; border-radius: 8px; background: rgba(40, 167, 69, 0.12); color: #28A745; font-size: 0.82rem; font-weight: 700;">
                  <i class="fa-solid fa-circle-check"></i> Added "${this.escapeHtml(act.task?.title || 'Task')}" & increased Total Budget to ${curr}${(parseFloat(act.newBudget || this.activeEvent?.budget || 0)).toLocaleString()}!
                </div>
              `;
            } else if (act.type === 'budget_added' || act.type === 'expense_updated') {
              contentHtml += `
                <div style="margin-top: 10px; padding: 8px 14px; border-radius: 8px; background: rgba(140, 83, 62, 0.12); color: var(--color-primary); font-size: 0.82rem; font-weight: 700;">
                  <i class="fa-solid fa-wallet"></i> Updated Budget Planner for "${this.escapeHtml(act.item?.category || 'Category')}"!
                </div>
              `;
            } else if (act.type === 'guest_added') {
              contentHtml += `
                <div style="margin-top: 10px; padding: 8px 14px; border-radius: 8px; background: rgba(212, 136, 36, 0.15); color: #D48824; font-size: 0.82rem; font-weight: 700;">
                  <i class="fa-solid fa-user-check"></i> Added Guest "${this.escapeHtml(act.guest?.name || 'Guest')}" to Directory!
                </div>
              `;
            } else if (act.type === 'event_created') {
              if (act.event) {
                const existingIdx = this.events.findIndex(e => e.id === act.event.id);
                if (existingIdx >= 0) {
                  this.events[existingIdx] = act.event;
                } else {
                  this.events.unshift(act.event);
                }
                this.switchEvent(act.event.id);
                this.showToast(`✨ Workspace for "${act.event.name}" created!`, 'success');
              }
              contentHtml += `
                <div style="margin-top: 10px; padding: 8px 14px; border-radius: 8px; background: rgba(140, 83, 62, 0.12); color: var(--color-primary); font-size: 0.82rem; font-weight: 700;">
                  <i class="fa-solid fa-wand-magic-sparkles"></i> Created Workspace for "${this.escapeHtml(act.event?.name || 'Celebration')}"!
                </div>
              `;
            }
            this.renderAll();
          }

          responseBubble.innerHTML = `
            <div class="chat-avatar-mini"><i class="fa-solid fa-wand-magic-sparkles"></i></div>
            <div class="chat-text">${contentHtml}</div>
          `;
          streamContainer.appendChild(responseBubble);

          // 2. Web Research Venue Cards (Section 2C)
          if (data.venues_research && data.venues_research.length > 0) {
            const venuesWrap = document.createElement('div');
            venuesWrap.style.marginTop = '12px';
            venuesWrap.style.display = 'flex';
            venuesWrap.style.flexDirection = 'column';
            venuesWrap.style.gap = '12px';

            data.venues_research.forEach(venue => {
              const card = document.createElement('div');
              card.className = 'venue-research-card';
              card.innerHTML = `
                <div class="vrc-header">
                  <span class="vrc-name"><i class="fa-solid fa-hotel"></i> ${this.escapeHtml(venue.name)}</span>
                  <span class="vrc-price-tag">${this.escapeHtml(venue.price_range || 'Contact for Quote')}</span>
                </div>
                <div class="vrc-meta-grid">
                  <div><strong>📍 Location:</strong> ${this.escapeHtml(venue.location)}</div>
                  <div><strong>👥 Capacity:</strong> ${this.escapeHtml(venue.capacity)}</div>
                  <div style="grid-column: 1 / -1;"><strong>✨ Facilities:</strong> ${this.escapeHtml(venue.facilities)}</div>
                </div>
                <div class="vrc-advantage"><strong>💡 Advantage:</strong> ${this.escapeHtml(venue.advantages)}</div>
                <div style="display:flex; align-items:center; justify-content:space-between; margin-top:10px;">
                  <a href="${venue.source_link || '#'}" target="_blank" rel="noopener noreferrer" class="vrc-btn-link">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> View Source / Contact
                  </a>
                  <button type="button" class="btn btn-primary btn-xs btn-add-venue-plan">
                    <i class="fa-solid fa-plus"></i> Add to My Plan
                  </button>
                </div>
              `;

              card.querySelector('.btn-add-venue-plan')?.addEventListener('click', async () => {
                await this.saveVenueToPlan(venue);
                const btn = card.querySelector('.btn-add-venue-plan');
                if (btn) {
                  btn.disabled = true;
                  btn.innerHTML = '<i class="fa-solid fa-check"></i> Added to Vendors';
                  btn.classList.replace('btn-primary', 'btn-outline');
                }
              });

              venuesWrap.appendChild(card);
            });
            responseBubble.querySelector('.chat-text').appendChild(venuesWrap);
          }

          // 3. Cost Estimation Breakdown Card (Section 2D)
          if (data.cost_estimation) {
            const est = data.cost_estimation;
            const cur = est.currency || '₹';
            const estCard = document.createElement('div');
            estCard.className = 'cost-estimate-card';

            let tableRows = '';
            (est.items || []).forEach(item => {
              tableRows += `
                <tr>
                  <td><strong>${this.escapeHtml(item.category)}</strong><br><small style="color:var(--text-muted);">${this.escapeHtml(item.notes || '')}</small></td>
                  <td style="text-align:right; font-weight:700;">${cur}${(item.estimated || 0).toLocaleString()}</td>
                </tr>
              `;
            });

            estCard.innerHTML = `
              <div class="cost-estimate-title">
                <i class="fa-solid fa-calculator"></i> ${this.escapeHtml(est.title || 'Estimated Budget Breakdown')}
              </div>
              <table class="cost-estimate-table">
                <thead>
                  <tr>
                    <th>Category & Deliverables</th>
                    <th style="text-align:right;">Approximate Cost</th>
                  </tr>
                </thead>
                <tbody>
                  ${tableRows}
                  <tr class="cost-estimate-total-row">
                    <td>TOTAL ESTIMATE</td>
                    <td style="text-align:right; color:var(--color-primary);">${cur}${(est.totalEstimated || 0).toLocaleString()}</td>
                  </tr>
                </tbody>
              </table>
              <button type="button" class="btn-add-budget-plan">
                <i class="fa-solid fa-table-list"></i> 1-Click Add to Budget Planner
              </button>
            `;

            estCard.querySelector('.btn-add-budget-plan')?.addEventListener('click', async () => {
              await this.applyCostEstimationToBudget(est);
              const bBtn = estCard.querySelector('.btn-add-budget-plan');
              if (bBtn) {
                bBtn.disabled = true;
                bBtn.innerHTML = '<i class="fa-solid fa-check"></i> Added to Budget Planner!';
                bBtn.style.background = '#28A745';
              }
            });

            responseBubble.querySelector('.chat-text').appendChild(estCard);
          }

          // 4. Recommendation Cards (Section 2E)
          if (data.recommendations && data.recommendations.length > 0) {
            data.recommendations.forEach(rec => {
              const recCard = document.createElement('div');
              recCard.className = 'ai-recommendation-card';
              recCard.innerHTML = `
                <div class="air-title"><i class="fa-solid fa-wand-magic-sparkles" style="color: var(--color-primary);"></i> ${this.escapeHtml(rec.title)}</div>
                <div class="air-desc">${this.escapeHtml(rec.description)}</div>
                <button type="button" class="btn-add-to-plan">
                  <i class="fa-solid fa-plus"></i> Add to My Plan
                </button>
              `;

              recCard.querySelector('.btn-add-to-plan')?.addEventListener('click', async () => {
                await this.applyAIRecommendation(rec);
                recCard.innerHTML = `
                  <div style="color: #28A745; font-size: 0.82rem; font-weight: 700;">
                    <i class="fa-solid fa-check-circle"></i> Added to your ${rec.type === 'budget' ? 'Budget' : 'Checklist'}!
                  </div>
                `;
              });
              responseBubble.querySelector('.chat-text').appendChild(recCard);
            });
          }

          streamContainer.scrollTop = streamContainer.scrollHeight;
        } else {
          loadingBubble.innerHTML = `<div class="chat-text" style="color:#DC3545;"><p>Could not process request. Please try again.</p></div>`;
        }
      } catch (err) {
        console.error('AI Query error:', err);
        loadingBubble.innerHTML = `<div class="chat-text"><p>I am your event coordinator. Try asking about venues, budget estimations, or task additions!</p></div>`;
      }
    },

    async saveVenueToPlan(venue) {
      if (!this.activeEvent) return;
      const vendorData = {
        name: venue.name,
        category: 'Venue & Reception',
        contact: venue.location || 'Direct booking',
        quotedPrice: 50000,
        advancePaid: 0,
        status: 'In Talks',
        notes: `Capacity: ${venue.capacity} • Facilities: ${venue.facilities} • Link: ${venue.source_link || ''}`
      };
      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/vendors`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(vendorData)
        });
        if (res.ok) {
          const data = await res.json();
          if (!this.activeEvent.vendors) this.activeEvent.vendors = [];
          this.activeEvent.vendors.push(data.vendor);
          this.renderOverviewStats();
          this.renderVendors();
          this.showToast(`✨ Saved "${venue.name}" to Vendor Directory!`, 'success');
        }
      } catch (e) {
        console.error('Save venue error:', e);
      }
    },

    async applyCostEstimationToBudget(est) {
      if (!this.activeEvent || !est.items) return;
      try {
        let addedCount = 0;
        for (const item of est.items) {
          const budgetData = {
            category: item.category,
            allocated: parseFloat(item.estimated) || 0,
            spent: 0,
            notes: item.notes || 'AI Cost Estimation Breakdown'
          };
          const res = await fetch(`/api/events/${this.activeEvent.id}/budget`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(budgetData)
          });
          if (res.ok) {
            const data = await res.json();
            if (!this.activeEvent.budgetItems) this.activeEvent.budgetItems = [];
            this.activeEvent.budgetItems.push(data.item);
            addedCount++;
          }
        }
        this.renderOverviewStats();
        this.renderBudget();
        this.showToast(`💰 Added ${addedCount} categories to Budget Planner!`, 'success');
      } catch (e) {
        console.error('Apply cost estimation error:', e);
      }
    },

    async applyAIRecommendation(rec) {
      if (!this.activeEvent || !rec.payload) return;
      try {
        if (rec.type === 'budget') {
          const res = await fetch(`/api/events/${this.activeEvent.id}/budget`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rec.payload)
          });
          if (res.ok) {
            const data = await res.json();
            if (!this.activeEvent.budgetItems) this.activeEvent.budgetItems = [];
            this.activeEvent.budgetItems.push(data.item);
            this.renderOverviewStats();
            this.renderBudget();
            this.showToast(`✨ Added "${rec.payload.category}" to Budget!`, 'success');
          }
        } else {
          const res = await fetch(`/api/events/${this.activeEvent.id}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rec.payload)
          });
          if (res.ok) {
            const data = await res.json();
            if (!this.activeEvent.tasks) this.activeEvent.tasks = [];
            this.activeEvent.tasks.push(data.task);
            this.renderOverviewStats();
            this.renderAsanaTasks();
            this.renderCalendar();
            this.showToast(`✨ Added "${rec.payload.title}" to Checklist!`, 'success');
          }
        }
      } catch (e) {
        console.error('Error applying recommendation:', e);
      }
    },

    /* ==========================================================================
       BUDGET PLANNER
       ========================================================================== */
    renderBudget() {
      if (!this.budgetTableBody || !this.activeEvent) return;

      const ev = this.activeEvent;
      const currency = ev.currency || '₹';
      const targetBudget = parseFloat(ev.budget) || 0;
      const items = ev.budgetItems || [];

      const totalAllocated = items.reduce((acc, b) => acc + (parseFloat(b.allocated) || 0), 0);
      const totalSpent = items.reduce((acc, b) => acc + (parseFloat(b.spent) || 0), 0);
      const remainingBuffer = targetBudget - totalSpent;

      if (this.budgetTargetValue) this.budgetTargetValue.textContent = `${currency}${targetBudget.toLocaleString()}`;
      if (this.budgetAllocatedValue) this.budgetAllocatedValue.textContent = `${currency}${totalAllocated.toLocaleString()}`;
      if (this.budgetSpentValue) this.budgetSpentValue.textContent = `${currency}${totalSpent.toLocaleString()}`;
      if (this.budgetAllocatedTag) {
        const allocPct = targetBudget > 0 ? Math.round((totalAllocated / targetBudget) * 100) : 0;
        this.budgetAllocatedTag.textContent = `${allocPct}% of target`;
      }
      if (this.budgetRemainingTag) {
        if (remainingBuffer < 0) {
          this.budgetRemainingTag.className = 'bk-tag warning';
          this.budgetRemainingTag.textContent = `${currency}${Math.abs(remainingBuffer).toLocaleString()} OVER BUDGET`;
        } else {
          this.budgetRemainingTag.className = 'bk-tag success';
          this.budgetRemainingTag.textContent = `${currency}${remainingBuffer.toLocaleString()} Buffer Remaining`;
        }
      }

      // Check for category warnings
      let overBudgetCount = 0;
      items.forEach(b => {
        if ((parseFloat(b.spent) || 0) > (parseFloat(b.allocated) || 0)) overBudgetCount++;
      });
      if (this.budgetWarningAlert) {
        if (remainingBuffer < 0 || overBudgetCount > 0) {
          this.budgetWarningAlert.style.display = 'flex';
          if (this.budgetWarningText) {
            this.budgetWarningText.textContent = remainingBuffer < 0
              ? `Warning: Total expenses have exceeded your planned budget by ${currency}${Math.abs(remainingBuffer).toLocaleString()}!`
              : `Notice: ${overBudgetCount} budget categor${overBudgetCount === 1 ? 'y has' : 'ies have'} exceeded planned allocations.`;
          }
        } else {
          this.budgetWarningAlert.style.display = 'none';
        }
      }

      this.budgetTableBody.innerHTML = '';
      if (items.length === 0) {
        this.budgetTableBody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; padding: 32px; color: var(--text-muted);">
              No budget categories added yet. Click "+ Add Category" to start tracking.
            </td>
          </tr>
        `;
        return;
      }

      items.forEach(b => {
        const alloc = parseFloat(b.allocated) || 0;
        const spent = parseFloat(b.spent) || 0;
        const diff = alloc - spent;
        const isOver = diff < 0;

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${this.escapeHtml(b.category)}</strong></td>
          <td>${currency}${alloc.toLocaleString()}</td>
          <td style="color: ${isOver ? '#DC3545' : 'inherit'}; font-weight: 700;">${currency}${spent.toLocaleString()}</td>
          <td style="color: ${isOver ? '#DC3545' : '#28A745'}; font-weight: 700;">
            ${isOver ? '-' : ''}${currency}${Math.abs(diff).toLocaleString()}
            ${isOver ? ' <span class="badge badge-warning" style="font-size:0.65rem;">OVER</span>' : ''}
          </td>
          <td><span style="font-size: 0.82rem; color: var(--text-muted);">${this.escapeHtml(b.notes || '—')}</span></td>
          <td>
            <div style="display: flex; gap: 6px;">
              <button class="btn btn-outline btn-xs btn-edit-b" title="Edit"><i class="fa-solid fa-pen"></i></button>
              <button class="btn btn-outline btn-xs btn-del-b" title="Delete"><i class="fa-solid fa-trash-can"></i></button>
            </div>
          </td>
        `;

        tr.querySelector('.btn-edit-b')?.addEventListener('click', () => this.openBudgetModal(b));
        tr.querySelector('.btn-del-b')?.addEventListener('click', () => this.deleteBudgetItem(b.id));

        this.budgetTableBody.appendChild(tr);
      });
    },

    openBudgetModal(item = null) {
      if (item) {
        if (this.budgetIdHidden) this.budgetIdHidden.value = item.id;
        if (this.budgetCatInput) this.budgetCatInput.value = item.category || '';
        if (this.budgetAllocInput) this.budgetAllocInput.value = item.allocated || '';
        if (this.budgetSpentInput) this.budgetSpentInput.value = item.spent || 0;
        if (this.budgetNotesInput) this.budgetNotesInput.value = item.notes || '';
      } else {
        if (this.budgetIdHidden) this.budgetIdHidden.value = '';
        if (this.budgetCatInput) this.budgetCatInput.value = '';
        if (this.budgetAllocInput) this.budgetAllocInput.value = '';
        if (this.budgetSpentInput) this.budgetSpentInput.value = '0';
        if (this.budgetNotesInput) this.budgetNotesInput.value = '';
      }
      this.openModal(this.modalAddBudget);
    },

    async handleSaveBudget() {
      if (!this.activeEvent) return;
      const category = this.budgetCatInput?.value.trim();
      const allocated = parseFloat(this.budgetAllocInput?.value || 0);
      const spent = parseFloat(this.budgetSpentInput?.value || 0);
      const notes = this.budgetNotesInput?.value.trim();
      const id = this.budgetIdHidden?.value || null;

      if (!category) {
        this.showToast('Please enter a category name.', 'error');
        return;
      }

      const itemData = { id, category, allocated, spent, notes };

      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/budget`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(itemData)
        });

        if (res.ok) {
          const data = await res.json();
          if (!this.activeEvent.budgetItems) this.activeEvent.budgetItems = [];
          const idx = this.activeEvent.budgetItems.findIndex(b => b.id === data.item.id);
          if (idx >= 0) this.activeEvent.budgetItems[idx] = data.item;
          else this.activeEvent.budgetItems.push(data.item);

          this.closeModal(this.modalAddBudget);
          this.showToast('✨ Budget category saved!', 'success');
          this.renderOverviewStats();
          this.renderBudget();
        }
      } catch (err) {
        this.showToast('Could not save budget category.', 'error');
      }
    },

    async deleteBudgetItem(itemId) {
      if (!this.activeEvent) return;
      if (!confirm('Delete this budget category?')) return;
      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/budget/${itemId}`, { method: 'DELETE' });
        if (res.ok) {
          this.activeEvent.budgetItems = (this.activeEvent.budgetItems || []).filter(b => b.id !== itemId);
          this.showToast('Budget category deleted', 'info');
          this.renderOverviewStats();
          this.renderBudget();
        }
      } catch (err) {}
    },

    /* ==========================================================================
       EVENT TIMELINE
       ========================================================================== */
    renderTimeline() {
      if (!this.timelinePhasesList || !this.activeEvent) return;
      const timeline = this.activeEvent.timeline || [];

      this.timelinePhasesList.innerHTML = '';
      if (timeline.length === 0) {
        this.timelinePhasesList.innerHTML = `
          <div style="text-align: center; padding: 32px; color: var(--text-muted);">
            No timeline checkpoints set yet. Click "+ Add Milestone" to build your celebration roadmap.
          </div>
        `;
        return;
      }

      timeline.forEach(tl => {
        const card = document.createElement('div');
        card.className = `timeline-phase-card ${tl.completed ? 'done' : ''}`;
        card.innerHTML = `
          <div class="tpc-left">
            <input type="checkbox" class="tpc-checkbox" ${tl.completed ? 'checked' : ''} title="Mark milestone complete">
            <div>
              <span class="tpc-phase-badge">${this.escapeHtml(tl.phase || tl.timeBefore || 'Phase')}</span>
              <div class="tpc-title">${this.escapeHtml(tl.title)}</div>
              <div class="tpc-date"><i class="fa-regular fa-calendar"></i> Target: ${tl.dueDate || 'TBD'}</div>
            </div>
          </div>
          <div>
            <button class="btn btn-outline btn-xs btn-del-tl" title="Remove"><i class="fa-solid fa-trash-can"></i></button>
          </div>
        `;

        card.querySelector('.tpc-checkbox')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.toggleTimelineStatus(tl.id);
        });
        card.querySelector('.btn-del-tl')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.deleteTimelineItem(tl.id);
        });

        this.timelinePhasesList.appendChild(card);
      });
    },

    openTimelineModal() {
      if (this.timelineIdHidden) this.timelineIdHidden.value = '';
      if (this.timelineTitleInput) this.timelineTitleInput.value = '';
      if (this.timelineDateInput) this.timelineDateInput.value = this.activeEvent?.date || '';
      this.openModal(this.modalAddTimeline);
    },

    async handleSaveTimeline() {
      if (!this.activeEvent) return;
      const phase = this.timelinePhaseInput?.value || 'Milestone';
      const title = this.timelineTitleInput?.value.trim();
      const dueDate = this.timelineDateInput?.value || '';

      if (!title) {
        this.showToast('Please enter a milestone title.', 'error');
        return;
      }

      const itemData = { phase, title, dueDate, completed: false };

      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/timeline`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(itemData)
        });

        if (res.ok) {
          const data = await res.json();
          if (!this.activeEvent.timeline) this.activeEvent.timeline = [];
          this.activeEvent.timeline.push(data.item);
          this.closeModal(this.modalAddTimeline);
          this.showToast('✨ Timeline checkpoint added!', 'success');
          this.renderTimeline();
        }
      } catch (err) {}
    },

    async toggleTimelineStatus(itemId) {
      if (!this.activeEvent) return;
      const item = (this.activeEvent.timeline || []).find(t => t.id === itemId);
      if (!item) return;

      item.completed = !item.completed;
      try {
        await fetch(`/api/events/${this.activeEvent.id}/timeline/${itemId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item)
        });
        this.renderTimeline();
      } catch (err) {}
    },

    async deleteTimelineItem(itemId) {
      if (!this.activeEvent) return;
      try {
        await fetch(`/api/events/${this.activeEvent.id}/timeline/${itemId}`, { method: 'DELETE' });
        this.activeEvent.timeline = (this.activeEvent.timeline || []).filter(t => t.id !== itemId);
        this.renderTimeline();
      } catch (err) {}
    },

    /* ==========================================================================
       GUEST MANAGEMENT
       ========================================================================== */
    renderGuests() {
      if (!this.guestsTableBody || !this.activeEvent) return;
      const guests = this.activeEvent.guestsList || [];

      // Update KPI banner
      const confirmed = guests.filter(g => g.rsvp === 'Confirmed');
      const pending = guests.filter(g => g.rsvp === 'Pending');
      const totalHeadcount = confirmed.reduce((acc, g) => acc + (parseInt(g.attendeesCount) || 1), 0);

      if (this.kpiGuestsTotal) this.kpiGuestsTotal.textContent = guests.length;
      if (this.kpiGuestsConfirmed) this.kpiGuestsConfirmed.textContent = confirmed.length;
      if (this.kpiGuestsPending) this.kpiGuestsPending.textContent = pending.length;
      if (this.kpiGuestsHeadcount) this.kpiGuestsHeadcount.textContent = totalHeadcount;

      this.guestsTableBody.innerHTML = '';
      if (guests.length === 0) {
        this.guestsTableBody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; padding: 32px; color: var(--text-muted);">
              No guests invited yet. Click "+ Add Guest" to start building your guest list.
            </td>
          </tr>
        `;
        return;
      }

      guests.forEach(g => {
        const rsvpClass = (g.rsvp || 'pending').toLowerCase();
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${this.escapeHtml(g.name)}</strong></td>
          <td>
            <div style="font-size: 0.8rem; color: var(--text-muted);">
              ${g.phone ? `<div><i class="fa-solid fa-phone"></i> ${this.escapeHtml(g.phone)}</div>` : ''}
              ${g.email ? `<div><i class="fa-solid fa-envelope"></i> ${this.escapeHtml(g.email)}</div>` : ''}
              ${!g.phone && !g.email ? '—' : ''}
            </div>
          </td>
          <td><span class="badge" style="font-size: 0.75rem;">${this.escapeHtml(g.category || 'Family')}</span></td>
          <td><strong>${g.attendeesCount || 1}</strong></td>
          <td><span class="status-pill ${rsvpClass}">${this.escapeHtml(g.rsvp || 'Pending')}</span></td>
          <td><span style="font-size: 0.82rem; color: var(--text-muted);">${this.escapeHtml(g.dietaryNotes || '—')}</span></td>
          <td>
            <button class="btn btn-outline btn-xs btn-del-guest" title="Remove"><i class="fa-solid fa-trash-can"></i></button>
          </td>
        `;

        tr.querySelector('.btn-del-guest')?.addEventListener('click', () => this.deleteGuest(g.id));
        this.guestsTableBody.appendChild(tr);
      });
    },

    openGuestModal() {
      if (this.guestIdHidden) this.guestIdHidden.value = '';
      if (this.guestNameInput) this.guestNameInput.value = '';
      if (this.guestPhoneInput) this.guestPhoneInput.value = '';
      if (this.guestEmailInput) this.guestEmailInput.value = '';
      if (this.guestCountInput) this.guestCountInput.value = '1';
      if (this.guestDietaryInput) this.guestDietaryInput.value = '';
      this.openModal(this.modalAddGuest);
    },

    async handleSaveGuest() {
      if (!this.activeEvent) return;
      const name = this.guestNameInput?.value.trim();
      const phone = this.guestPhoneInput?.value.trim();
      const email = this.guestEmailInput?.value.trim();
      const rsvp = this.guestRsvpInput?.value || 'Pending';
      const attendeesCount = parseInt(this.guestCountInput?.value || '1');
      const category = this.guestCategoryInput?.value || 'Family';
      const dietaryNotes = this.guestDietaryInput?.value.trim();

      if (!name) {
        this.showToast('Please enter guest name.', 'error');
        return;
      }

      const guestData = { name, phone, email, rsvp, attendeesCount, category, dietaryNotes };

      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/guests`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(guestData)
        });

        if (res.ok) {
          const data = await res.json();
          if (!this.activeEvent.guestsList) this.activeEvent.guestsList = [];
          this.activeEvent.guestsList.push(data.guest);
          this.closeModal(this.modalAddGuest);
          this.showToast(`✨ Guest "${name}" added to list!`, 'success');
          this.renderOverviewStats();
          this.renderGuests();
        }
      } catch (err) {}
    },

    async deleteGuest(guestId) {
      if (!this.activeEvent) return;
      if (!confirm('Remove this guest from the invitation list?')) return;
      try {
        await fetch(`/api/events/${this.activeEvent.id}/guests/${guestId}`, { method: 'DELETE' });
        this.activeEvent.guestsList = (this.activeEvent.guestsList || []).filter(g => g.id !== guestId);
        this.renderOverviewStats();
        this.renderGuests();
      } catch (err) {}
    },

    /* ==========================================================================
       VENDOR DIRECTORY
       ========================================================================== */
    renderVendors() {
      if (!this.vendorsTableBody || !this.activeEvent) return;
      const vendors = this.activeEvent.vendors || [];
      const currency = this.activeEvent.currency || '₹';

      // Update KPI
      const totalQuoted = vendors.reduce((acc, v) => acc + (parseFloat(v.quotedPrice) || 0), 0);
      const totalPaid = vendors.reduce((acc, v) => acc + (parseFloat(v.advancePaid) || 0), 0);
      const totalBalance = totalQuoted - totalPaid;

      if (this.kpiVendorsCount) this.kpiVendorsCount.textContent = vendors.length;
      if (this.kpiVendorsQuoted) this.kpiVendorsQuoted.textContent = `${currency}${totalQuoted.toLocaleString()}`;
      if (this.kpiVendorsPaid) this.kpiVendorsPaid.textContent = `${currency}${totalPaid.toLocaleString()}`;
      if (this.kpiVendorsBalance) this.kpiVendorsBalance.textContent = `${currency}${Math.max(0, totalBalance).toLocaleString()}`;

      this.vendorsTableBody.innerHTML = '';
      if (vendors.length === 0) {
        this.vendorsTableBody.innerHTML = `
          <tr>
            <td colspan="8" style="text-align: center; padding: 32px; color: var(--text-muted);">
              No vendor partners listed yet. Click "+ Add Vendor" to add caterers, photographers, decorators and more.
            </td>
          </tr>
        `;
        return;
      }

      vendors.forEach(v => {
        const quoted = parseFloat(v.quotedPrice) || 0;
        const paid = parseFloat(v.advancePaid) || 0;
        const bal = quoted - paid;
        const statusClass = (v.status || 'in-talks').toLowerCase().replace(' ', '-');

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${this.escapeHtml(v.name)}</strong></td>
          <td><span class="badge" style="font-size: 0.75rem;">${this.escapeHtml(v.category || 'Service')}</span></td>
          <td><span style="font-size: 0.82rem; color: var(--text-muted);">${this.escapeHtml(v.contact || '—')}</span></td>
          <td>${currency}${quoted.toLocaleString()}</td>
          <td style="color: #28A745; font-weight: 700;">${currency}${paid.toLocaleString()}</td>
          <td style="color: ${bal > 0 ? '#D32F2F' : '#28A745'}; font-weight: 700;">${currency}${Math.max(0, bal).toLocaleString()}</td>
          <td><span class="status-pill ${statusClass}">${this.escapeHtml(v.status || 'In Talks')}</span></td>
          <td>
            <button class="btn btn-outline btn-xs btn-del-v" title="Remove"><i class="fa-solid fa-trash-can"></i></button>
          </td>
        `;

        tr.querySelector('.btn-del-v')?.addEventListener('click', () => this.deleteVendor(v.id));
        this.vendorsTableBody.appendChild(tr);
      });
    },

    openVendorModal() {
      if (this.vendorIdHidden) this.vendorIdHidden.value = '';
      if (this.vendorNameInput) this.vendorNameInput.value = '';
      if (this.vendorCategoryInput) this.vendorCategoryInput.value = '';
      if (this.vendorContactInput) this.vendorContactInput.value = '';
      if (this.vendorQuotedInput) this.vendorQuotedInput.value = '';
      if (this.vendorAdvanceInput) this.vendorAdvanceInput.value = '0';
      if (this.vendorNotesInput) this.vendorNotesInput.value = '';
      this.openModal(this.modalAddVendor);
    },

    async handleSaveVendor() {
      if (!this.activeEvent) return;
      const name = this.vendorNameInput?.value.trim();
      const category = this.vendorCategoryInput?.value.trim() || 'General';
      const contact = this.vendorContactInput?.value.trim();
      const quotedPrice = parseFloat(this.vendorQuotedInput?.value || 0);
      const advancePaid = parseFloat(this.vendorAdvanceInput?.value || 0);
      const status = this.vendorStatusInput?.value || 'In Talks';
      const notes = this.vendorNotesInput?.value.trim();

      if (!name) {
        this.showToast('Please enter vendor business name.', 'error');
        return;
      }

      const vendorData = { name, category, contact, quotedPrice, advancePaid, status, notes };

      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/vendors`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(vendorData)
        });

        if (res.ok) {
          const data = await res.json();
          if (!this.activeEvent.vendors) this.activeEvent.vendors = [];
          this.activeEvent.vendors.push(data.vendor);
          this.closeModal(this.modalAddVendor);
          this.showToast(`✨ Vendor "${name}" saved!`, 'success');
          this.renderOverviewStats();
          this.renderVendors();
        }
      } catch (err) {}
    },

    async deleteVendor(vendorId) {
      if (!this.activeEvent) return;
      if (!confirm('Remove this vendor from your directory?')) return;
      try {
        await fetch(`/api/events/${this.activeEvent.id}/vendors/${vendorId}`, { method: 'DELETE' });
        this.activeEvent.vendors = (this.activeEvent.vendors || []).filter(v => v.id !== vendorId);
        this.renderOverviewStats();
        this.renderVendors();
      } catch (err) {}
    },

    /* ==========================================================================
       NOTES & INSPIRATION
       ========================================================================== */
    renderNotes() {
      if (!this.notesCardsGrid || !this.activeEvent) return;
      const notes = this.activeEvent.notesList || [];

      this.notesCardsGrid.innerHTML = '';
      if (notes.length === 0) {
        this.notesCardsGrid.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 36px; color: var(--text-muted);">
            <i class="fa-solid fa-lightbulb" style="font-size: 2rem; margin-bottom: 12px; color: #D48824;"></i>
            <h4>No inspiration notes yet</h4>
            <p>Save color palettes, floral concepts, shopping lists and ideas here.</p>
          </div>
        `;
        return;
      }

      notes.forEach(n => {
        const card = document.createElement('div');
        card.className = 'note-card-box';
        card.innerHTML = `
          <div>
            <div class="note-card-header">
              <span class="note-tag-badge">${this.escapeHtml(n.tag || 'Idea')}</span>
              <button class="btn btn-outline btn-xs btn-del-note" title="Delete"><i class="fa-solid fa-trash-can"></i></button>
            </div>
            <div class="note-card-title">${this.escapeHtml(n.title)}</div>
            <div class="note-card-content">${this.escapeHtml(n.content)}</div>
          </div>
          <div class="note-card-footer">
            <span><i class="fa-regular fa-clock"></i> ${n.createdAt || ''}</span>
          </div>
        `;

        card.querySelector('.btn-del-note')?.addEventListener('click', () => this.deleteNote(n.id));
        this.notesCardsGrid.appendChild(card);
      });
    },

    openNoteModal() {
      if (this.noteIdHidden) this.noteIdHidden.value = '';
      if (this.noteTitleInput) this.noteTitleInput.value = '';
      if (this.noteContentInput) this.noteContentInput.value = '';
      this.openModal(this.modalAddNote);
    },

    async handleSaveNote() {
      if (!this.activeEvent) return;
      const title = this.noteTitleInput?.value.trim();
      const tag = this.noteTagInput?.value || 'Inspiration';
      const content = this.noteContentInput?.value.trim();

      if (!title || !content) {
        this.showToast('Please provide a title and note content.', 'error');
        return;
      }

      const noteData = { title, tag, content, createdAt: new Date().toISOString().split('T')[0] };

      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/notes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(noteData)
        });

        if (res.ok) {
          const data = await res.json();
          if (!this.activeEvent.notesList) this.activeEvent.notesList = [];
          this.activeEvent.notesList.unshift(data.note);
          this.closeModal(this.modalAddNote);
          this.showToast('✨ Idea saved to your board!', 'success');
          this.renderNotes();
        }
      } catch (err) {}
    },

    async deleteNote(noteId) {
      if (!this.activeEvent) return;
      try {
        await fetch(`/api/events/${this.activeEvent.id}/notes/${noteId}`, { method: 'DELETE' });
        this.activeEvent.notesList = (this.activeEvent.notesList || []).filter(n => n.id !== noteId);
        this.renderNotes();
      } catch (err) {}
    },

    /* ==========================================================================
       AUTHENTIC 3D PAGE-TURNING KEEPSAKE DIARY
       ========================================================================== */
    renderDiaryBookSpread() {
      if (!this.diaryBookSpread || !this.activeEvent) return;
      const entries = this.activeEvent.diaryEntries || [];

      // Render chapters index
      if (this.bookChaptersList) {
        this.bookChaptersList.innerHTML = '';
        if (entries.length === 0) {
          this.bookChaptersList.innerHTML = `<li style="color: var(--text-muted); font-size: 0.8rem; padding: 6px;">No entries written yet</li>`;
        } else {
          entries.forEach((e, idx) => {
            const li = document.createElement('li');
            li.className = `book-chapter-item ${idx === this.currentDiaryPageIndex ? 'active' : ''}`;
            li.innerHTML = `
              <span class="bci-title">${this.escapeHtml(e.title || 'Untitled')}</span>
              <span class="bci-date">${e.date || ''}</span>
            `;
            li.addEventListener('click', () => {
              this.currentDiaryPageIndex = idx;
              this.renderDiaryBookSpread();
            });
            this.bookChaptersList.appendChild(li);
          });
        }
      }

      // Page numbers
      const totalPages = Math.max(1, entries.length);
      const currentPage = this.currentDiaryPageIndex + 1;
      if (this.leftPageNumber) this.leftPageNumber.textContent = `Page ${this.currentDiaryPageIndex * 2 + 1}`;
      if (this.rightPageNumber) this.rightPageNumber.textContent = `Page ${this.currentDiaryPageIndex * 2 + 2}`;
      if (this.bookPageIndicator) this.bookPageIndicator.textContent = `Entry ${currentPage} of ${totalPages}`;

      // If viewing existing entry
      if (entries.length > 0 && this.currentDiaryPageIndex < entries.length) {
        const cur = entries[this.currentDiaryPageIndex];
        if (this.diaryInputDate) this.diaryInputDate.value = cur.date || '';
        if (this.diarySelectMood) this.diarySelectMood.value = cur.mood || 'Heartfelt';
        if (this.diaryInputTitle) this.diaryInputTitle.value = cur.title || '';
        if (this.diaryInputContent) this.diaryInputContent.value = cur.content || '';
        if (this.btnSaveDiaryEntry) this.btnSaveDiaryEntry.textContent = 'Update Keepsake Page';

        // Apply entry's saved stationery pattern
        if (cur.pattern) this.setDiaryPattern(cur.pattern, false);
      } else {
        // New Blank Entry Page
        if (this.diaryInputDate) this.diaryInputDate.value = new Date().toISOString().split('T')[0];
        if (this.diarySelectMood) this.diarySelectMood.value = 'Joyful';
        if (this.diaryInputTitle) this.diaryInputTitle.value = '';
        if (this.diaryInputContent) this.diaryInputContent.value = '';
        if (this.btnSaveDiaryEntry) this.btnSaveDiaryEntry.textContent = 'Preserve in Diary';
      }
    },

    turnDiaryPage(direction) {
      const entries = this.activeEvent?.diaryEntries || [];
      const newIdx = this.currentDiaryPageIndex + direction;
      if (newIdx >= 0 && newIdx < entries.length) {
        this.currentDiaryPageIndex = newIdx;
        this.renderDiaryBookSpread();
      }
    },

    turnToNewEntryPage() {
      const entries = this.activeEvent?.diaryEntries || [];
      this.currentDiaryPageIndex = entries.length;
      this.renderDiaryBookSpread();
    },

    async handleSaveDiary() {
      if (!this.activeEvent) return;
      const date = this.diaryInputDate?.value || new Date().toISOString().split('T')[0];
      const mood = this.diarySelectMood?.value || 'Heartfelt';
      const title = this.diaryInputTitle?.value.trim() || 'Cherished Memory';
      const content = this.diaryInputContent?.value.trim();
      const pattern = this.activeDiaryPattern || 'pattern_kitty.png';

      if (!content) {
        this.showToast('Please write some thoughts before preserving!', 'error');
        return;
      }

      const entries = this.activeEvent.diaryEntries || [];
      const isExisting = (this.currentDiaryPageIndex < entries.length);
      const existingId = isExisting ? entries[this.currentDiaryPageIndex].id : null;

      const diaryData = { id: existingId, date, mood, title, content, pattern };

      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/diary`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(diaryData)
        });

        if (res.ok) {
          const data = await res.json();
          if (isExisting) entries[this.currentDiaryPageIndex] = data.entry;
          else {
            entries.unshift(data.entry);
            this.currentDiaryPageIndex = 0;
          }
          this.activeEvent.diaryEntries = entries;
          this.showToast('📖 Preserved in your Keepsake Diary!', 'success');
          this.renderDiaryBookSpread();
        }
      } catch (err) {}
    },

    setDiaryPattern(patternFile, persist = true) {
      if (!patternFile) patternFile = 'pattern_kitty.png';
      this.activeDiaryPattern = patternFile;

      if (this.diaryStationeryFrame) {
        this.diaryStationeryFrame.style.backgroundImage = `url('assets/patterns/${patternFile}')`;
      }

      const patternNames = {
        'pattern_kitty.png': 'Cozy Kitty',
        'pattern_hearts.svg': 'Sweet Hearts',
        'pattern_check.svg': 'Pastel Gingham',
        'pattern_stars.svg': 'Celestial Stars',
        'pattern_floral.svg': 'Spring Blossom',
        'pattern_polka.svg': 'Peach Confetti',
        'pattern_lavender.svg': 'Lavender Herbs',
        'pattern_lotus.png': 'Lotus Pond',
        'pattern_duckling.png': 'Sunny Duckling'
      };
      const name = patternNames[patternFile] || 'Pattern Frame';
      if (this.sidebarDiaryBadge) this.sidebarDiaryBadge.textContent = name;

      this.patPills?.forEach(pill => {
        if (pill.getAttribute('data-pattern') === patternFile) pill.classList.add('active');
        else pill.classList.remove('active');
      });

      if (persist) {
        fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pattern: patternFile })
        }).catch(() => {});
      }
    },

    /* ==========================================================================
       THEMES
       ========================================================================== */
    applyTheme(theme, persist = true) {
      this.activeTheme = theme;
      document.body.setAttribute('data-theme', theme);

      const themeNames = {
        'kitty-cozy': 'Cozy Kitty',
        'lotus-serenity': 'Lotus Serenity',
        'duckling-sunny': 'Sunny Duckling',
        'lavender-soft': 'Soft Lavender',
        'midnight-luxe': 'Midnight Starry'
      };
      const name = themeNames[theme] || 'Cozy Kitty';
      if (this.sidebarThemeName) this.sidebarThemeName.textContent = `${name} Theme`;
      if (this.activeThemeBadge) this.activeThemeBadge.textContent = `Active: ${name}`;

      this.themeMoodCards?.forEach(card => {
        const cTheme = card.getAttribute('data-theme');
        const btn = card.querySelector('.btn-apply-theme');
        if (cTheme === theme) {
          card.classList.add('active');
          if (btn) {
            btn.className = 'btn btn-primary btn-sm btn-apply-theme';
            btn.textContent = 'Active';
          }
        } else {
          card.classList.remove('active');
          if (btn) {
            btn.className = 'btn btn-outline btn-sm btn-apply-theme';
            btn.textContent = 'Apply';
          }
        }
      });

      if (persist) {
        this.showToast(`✨ Palette ambiance changed to ${name}!`, 'success');
        fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ theme })
        }).catch(() => {});
      }
    },

    /* ==========================================================================
       WORKSPACE SUB-NAVIGATION & ACTIVE PANES (IN DASHBOARD)
       ========================================================================== */
    switchWsPane(paneId) {
      this.currentWsPane = paneId || 'overview';
      this.wsSubnavPills?.forEach(pill => {
        if (pill.getAttribute('data-ws-pane') === this.currentWsPane) {
          pill.classList.add('active');
        } else {
          pill.classList.remove('active');
        }
      });

      this.wsPanes?.forEach(pane => {
        if (pane.id === `ws-pane-${this.currentWsPane}`) {
          pane.classList.add('active');
        } else {
          pane.classList.remove('active');
        }
      });

      if (this.floatingAiContextBadge) {
        const labels = {
          overview: 'Overview & Cal',
          tasks: 'Tasks Checklist',
          budget: 'Budget Optimizer',
          timeline: 'Timeline',
          guests: 'Guest Management',
          vendors: 'Vendors Directory',
          notes: 'Notes & Ideas',
          diary: 'Keepsake Diary'
        };
        this.floatingAiContextBadge.textContent = labels[this.currentWsPane] || 'Workspace';
      }

      const titles = {
        overview: 'Overview & Calendar',
        tasks: 'Tasks & Checklist',
        budget: 'Budget Optimizer',
        timeline: 'Event Timeline',
        guests: 'Guest Management',
        vendors: 'Vendor Directory',
        notes: 'Notes & Ideas',
        diary: 'Keepsake Diary'
      };
      if (this.currentSectionTitle) {
        this.currentSectionTitle.textContent = titles[this.currentWsPane] || 'Overview';
      }

      // Re-render corresponding sub-section
      if (this.currentWsPane === 'overview') {
        this.renderOverviewHero();
        this.renderOverviewStats();
        this.renderCalendar();
        this.renderReminders();
      } else if (this.currentWsPane === 'tasks') {
        this.renderAsanaTasks();
      } else if (this.currentWsPane === 'budget') {
        this.renderBudget();
      } else if (this.currentWsPane === 'timeline') {
        this.renderTimeline();
      } else if (this.currentWsPane === 'guests') {
        this.renderGuests();
      } else if (this.currentWsPane === 'vendors') {
        this.renderVendors();
      } else if (this.currentWsPane === 'notes') {
        this.renderNotes();
      } else if (this.currentWsPane === 'diary') {
        this.renderDiaryBookSpread();
      }
    },

    updateCopilotContextBanner() {
      if (!this.activeEvent) return;
      if (this.copilotActiveEventName) this.copilotActiveEventName.textContent = this.activeEvent.name;
      if (this.copilotActiveEventType) this.copilotActiveEventType.textContent = this.activeEvent.type || 'Event';
      if (this.copilotActiveLocation) this.copilotActiveLocation.textContent = this.activeEvent.location || 'Location TBD';
      if (this.copilotActiveBudget) {
        const cur = this.activeEvent.currency || '₹';
        const b = parseFloat(this.activeEvent.budget) || 0;
        this.copilotActiveBudget.textContent = `${cur}${b.toLocaleString()}`;
      }
      if (this.copilotStreamEventName) this.copilotStreamEventName.textContent = this.activeEvent.name;

      // Dynamically adapt copilot quick prompt chips to active event location, guests, and type
      const locParts = (this.activeEvent.location || 'Chennai').split(',');
      const city = locParts[locParts.length - 1].trim() || 'Chennai';
      const guests = this.activeEvent.guests || 300;
      const type = this.activeEvent.type || 'wedding';

      const chipVenues = document.getElementById('chipDedicatedVenues');
      const chipVenuesLabel = document.getElementById('chipDedicatedVenuesLabel');
      if (chipVenues && chipVenuesLabel) {
        chipVenues.setAttribute('data-dedicated-prompt', `🔍 Suggest best ${type.toLowerCase()} venues in ${city} with pricing, capacity, and facilities`);
        chipVenuesLabel.textContent = `🏛️ Venues in ${city}`;
      }

      const chipEstimate = document.getElementById('chipDedicatedEstimate');
      const chipEstimateLabel = document.getElementById('chipDedicatedEstimateLabel');
      if (chipEstimate && chipEstimateLabel) {
        chipEstimate.setAttribute('data-dedicated-prompt', `💰 Estimate realistic budget breakdown for ${guests} guests with category allocations`);
        chipEstimateLabel.textContent = `💰 ${guests}-Guest Budget Breakdown`;
      }
    },

    /* ==========================================================================
       REMINDERS & DEADLINES WIDGET (SECTION 4)
       ========================================================================== */
    renderReminders() {
      if (!this.remindersList || !this.activeEvent) return;
      const reminders = this.activeEvent.reminders || [];
      this.remindersList.innerHTML = '';

      if (reminders.length === 0) {
        this.remindersList.innerHTML = `
          <div style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.88rem;">
            <i class="fa-regular fa-bell-slash" style="font-size: 1.6rem; opacity: 0.5; margin-bottom: 6px; display: block;"></i>
            No upcoming reminders set for this celebration yet.
            <div style="margin-top: 8px;">
              <button class="btn btn-outline btn-xs" id="btnRemindersEmptyAdd">
                <i class="fa-solid fa-plus"></i> Add Reminder
              </button>
            </div>
          </div>
        `;
        this.remindersList.querySelector('#btnRemindersEmptyAdd')?.addEventListener('click', () => {
          this.openAddReminderModal();
        });
        return;
      }

      const todayStr = new Date().toISOString().split('T')[0];

      reminders.forEach(rem => {
        const isDone = rem.status === 'completed';
        const isOverdue = !isDone && rem.dueDate && rem.dueDate < todayStr;
        const priorityBadges = {
          'High': '<span class="priority-badge high">🔴 High</span>',
          'Medium': '<span class="priority-badge medium">🟡 Med</span>',
          'Low': '<span class="priority-badge low">🟢 Low</span>'
        };
        const pBadge = priorityBadges[rem.priority] || '<span class="priority-badge medium">🟡 Med</span>';

        const row = document.createElement('div');
        row.className = `reminder-item-row ${isDone ? 'completed' : ''} ${isOverdue ? 'overdue' : ''}`;
        row.innerHTML = `
          <input type="checkbox" class="reminder-checkbox" ${isDone ? 'checked' : ''} title="Mark done">
          <div class="reminder-body">
            <div class="reminder-title">${this.escapeHtml(rem.title)}</div>
            <div class="reminder-meta-row">
              <span class="reminder-date"><i class="fa-regular fa-clock"></i> ${this.formatReminderDate(rem.dueDate, rem.dueTime)}</span>
              ${pBadge}
              ${isOverdue ? '<span class="reminder-overdue-tag">⚠️ Overdue</span>' : ''}
              ${rem.notes ? `<span class="reminder-notes-hint" title="${this.escapeHtml(rem.notes)}"><i class="fa-solid fa-circle-info"></i> Notes</span>` : ''}
            </div>
          </div>
          <div class="reminder-actions">
            <button class="btn-icon-subtle btn-edit-reminder" title="Edit reminder"><i class="fa-solid fa-pen"></i></button>
            <button class="btn-icon-subtle btn-del-reminder" title="Delete reminder"><i class="fa-solid fa-trash-can"></i></button>
          </div>
        `;

        row.querySelector('.reminder-checkbox')?.addEventListener('change', (e) => {
          this.handleToggleReminder(rem.id, e.target.checked);
        });
        row.querySelector('.btn-edit-reminder')?.addEventListener('click', () => {
          this.openAddReminderModal(rem);
        });
        row.querySelector('.btn-del-reminder')?.addEventListener('click', () => {
          this.handleDeleteReminder(rem.id);
        });

        this.remindersList.appendChild(row);
      });
    },

    formatReminderDate(dStr, tStr) {
      if (!dStr) return 'No date';
      try {
        const parts = dStr.split('-');
        if (parts.length === 3) {
          const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
          const m = months[parseInt(parts[1], 10) - 1];
          const time = tStr ? ` at ${tStr}` : '';
          return `${m} ${parseInt(parts[2], 10)}, ${parts[0]}${time}`;
        }
      } catch (e) {}
      return `${dStr} ${tStr || ''}`;
    },

    openAddReminderModal(rem = null) {
      if (!this.modalAddReminder) return;
      if (this.formReminder) this.formReminder.reset();

      if (rem) {
        if (this.reminderModalHeading) this.reminderModalHeading.textContent = 'Edit Reminder';
        if (this.reminderIdHidden) this.reminderIdHidden.value = rem.id;
        if (this.reminderTitleInput) this.reminderTitleInput.value = rem.title || '';
        if (this.reminderDateInput) this.reminderDateInput.value = rem.dueDate || '';
        if (this.reminderTimeInput) this.reminderTimeInput.value = rem.dueTime || '10:00';
        if (this.reminderPriorityInput) this.reminderPriorityInput.value = rem.priority || 'Medium';
        if (this.reminderNotesInput) this.reminderNotesInput.value = rem.notes || '';
      } else {
        if (this.reminderModalHeading) this.reminderModalHeading.textContent = 'Add Reminder';
        if (this.reminderIdHidden) this.reminderIdHidden.value = '';
        if (this.reminderDateInput) {
          const d = new Date();
          d.setDate(d.getDate() + 2);
          this.reminderDateInput.value = d.toISOString().split('T')[0];
        }
        if (this.reminderTimeInput) this.reminderTimeInput.value = '10:00';
      }
      this.openModal(this.modalAddReminder);
    },

    async handleSaveReminder() {
      if (!this.activeEvent) return;
      const title = this.reminderTitleInput?.value.trim();
      const dueDate = this.reminderDateInput?.value;
      if (!title || !dueDate) {
        this.showToast('Please provide a title and due date', 'error');
        return;
      }
      const remId = this.reminderIdHidden?.value;
      const payload = {
        title,
        dueDate,
        dueTime: this.reminderTimeInput?.value || '10:00',
        priority: this.reminderPriorityInput?.value || 'Medium',
        notes: this.reminderNotesInput?.value.trim() || '',
        status: 'pending'
      };

      try {
        const method = remId ? 'PUT' : 'POST';
        const url = remId 
          ? `/api/events/${this.activeEvent.id}/reminders/${remId}`
          : `/api/events/${this.activeEvent.id}/reminders`;

        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          if (data.event) {
            this.activeEvent = data.event;
          } else if (data.reminder) {
            if (!this.activeEvent.reminders) this.activeEvent.reminders = [];
            if (remId) {
              const idx = this.activeEvent.reminders.findIndex(r => r.id === remId);
              if (idx >= 0) this.activeEvent.reminders[idx] = data.reminder;
            } else {
              this.activeEvent.reminders.push(data.reminder);
            }
          }
          this.closeModal(this.modalAddReminder);
          this.renderReminders();
          this.showToast(`🔔 Reminder saved successfully!`, 'success');
        } else {
          this.showToast('Failed to save reminder', 'error');
        }
      } catch (err) {
        console.error('Error saving reminder:', err);
        this.showToast('Error saving reminder', 'error');
      }
    },

    async handleToggleReminder(remId, isCompleted) {
      if (!this.activeEvent) return;
      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/reminders/${remId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: isCompleted ? 'completed' : 'pending' })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.event) this.activeEvent = data.event;
          else {
            const r = (this.activeEvent.reminders || []).find(item => item.id === remId);
            if (r) r.status = isCompleted ? 'completed' : 'pending';
          }
          this.renderReminders();
        }
      } catch (err) {
        console.error('Toggle reminder error:', err);
      }
    },

    async handleDeleteReminder(remId) {
      if (!this.activeEvent) return;
      if (!confirm('Are you sure you want to remove this reminder?')) return;
      try {
        const res = await fetch(`/api/events/${this.activeEvent.id}/reminders/${remId}`, {
          method: 'DELETE'
        });
        if (res.ok) {
          this.activeEvent.reminders = (this.activeEvent.reminders || []).filter(r => r.id !== remId);
          this.renderReminders();
          this.showToast('Reminder deleted', 'info');
        }
      } catch (err) {
        console.error('Delete reminder error:', err);
      }
    },

    /* ==========================================================================
       MY EVENTS HUB & EVENT EDIT/DELETE (SECTION 1 & 6)
       ========================================================================== */
    renderMyEvents() {
      if (!this.eventsManagerGrid) return;
      if (this.badgeEventsCount) {
        this.badgeEventsCount.textContent = this.events.length;
      }
      this.eventsManagerGrid.innerHTML = '';

      if (this.events.length === 0) {
        this.eventsManagerGrid.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 40px; text-align: center; color: var(--text-muted);">
            <h3>No celebrations found</h3>
            <p>Create your first event workspace to start planning.</p>
          </div>
        `;
        return;
      }

      this.events.forEach(ev => {
        const evId = ev.id || ev._id;
        if (!evId || evId === 'undefined') return;
        const isActive = this.activeEvent && (this.activeEvent.id === evId || this.activeEvent._id === evId);
        const bItems = ev.budgetItems || [];
        const totalSpent = bItems.reduce((acc, b) => acc + (parseFloat(b.spent) || 0), 0);
        const totalBudget = parseFloat(ev.budget) || 1;
        const pct = Math.min(100, Math.round((totalSpent / totalBudget) * 100));
        const countdown = this.calculateDaysRemaining(ev.date);

        const card = document.createElement('div');
        card.className = `event-manage-card ${isActive ? 'active-event' : ''}`;
        card.innerHTML = `
          <div class="emc-header">
            <span class="emc-type-pill">${this.escapeHtml(ev.type || 'Event')}</span>
            ${isActive ? '<span class="emc-active-badge">● Active Workspace</span>' : `<span class="ehb-countdown-badge" style="font-size:0.75rem;">${countdown.text}</span>`}
          </div>
          <h3 class="emc-title">${this.escapeHtml(ev.name)}</h3>
          <div class="emc-meta-row">
            <span class="emc-meta-item"><i class="fa-regular fa-calendar"></i> ${this.escapeHtml(ev.date || 'TBD')}</span>
            <span class="emc-meta-item"><i class="fa-solid fa-location-dot"></i> ${this.escapeHtml(ev.location || 'Location TBD')}</span>
            <span class="emc-meta-item"><i class="fa-solid fa-user-group"></i> ${ev.guests || 0} Guests • ${this.escapeHtml(ev.duration || '1 Day')}</span>
          </div>
          <div class="emc-progress-wrap">
            <div class="emc-progress-info">
              <span>Budget: ${ev.currency || '₹'}${totalSpent.toLocaleString()} / ${ev.currency || '₹'}${totalBudget.toLocaleString()}</span>
              <span>${pct}%</span>
            </div>
            <div class="omc-progress-track">
              <div class="omc-progress-bar" style="width: ${pct}%;"></div>
            </div>
          </div>
          <div class="emc-actions">
            <button class="btn ${isActive ? 'btn-primary' : 'btn-outline'} btn-sm btn-open-ws" style="flex:1;">
              <i class="fa-solid fa-arrow-right-to-bracket"></i> ${isActive ? 'Current Workspace' : 'Open Workspace'}
            </button>
            <button class="btn btn-outline btn-sm btn-edit-ev" title="Edit Event"><i class="fa-solid fa-pen"></i></button>
            <button class="btn btn-outline btn-sm btn-del-ev text-danger" title="Delete Event"><i class="fa-solid fa-trash-can"></i></button>
          </div>
        `;

        card.querySelector('.btn-open-ws')?.addEventListener('click', () => {
          this.switchActiveEvent(evId);
          this.switchTab('dashboard');
        });
        card.querySelector('.btn-edit-ev')?.addEventListener('click', () => {
          this.openEditEventModal(ev);
        });
        card.querySelector('.btn-del-ev')?.addEventListener('click', () => {
          this.handleDeleteEvent(evId);
        });

        this.eventsManagerGrid.appendChild(card);
      });
    },

    openEditEventModal(ev = null) {
      const target = ev || this.activeEvent;
      if (!target || !this.modalEditEvent) return;

      if (this.editEventIdHidden) this.editEventIdHidden.value = target.id;
      if (this.editEventName) this.editEventName.value = target.name || '';
      if (this.editEventType) this.editEventType.value = target.type || 'Wedding';
      if (this.editEventDate) this.editEventDate.value = target.date || '';
      if (this.editEventLocation) this.editEventLocation.value = target.location || '';
      if (this.editEventGuests) this.editEventGuests.value = target.guests || 100;
      if (this.editEventCurrency) this.editEventCurrency.value = target.currency || '₹';
      if (this.editEventBudget) this.editEventBudget.value = target.budget || 50000;
      if (this.editEventDuration) this.editEventDuration.value = target.duration || '1 Day';
      if (this.editEventNotes) this.editEventNotes.value = target.notes || '';

      this.openModal(this.modalEditEvent);
    },

    async handleSaveEditEvent() {
      const eventId = this.editEventIdHidden?.value;
      if (!eventId) return;

      const name = this.editEventName?.value.trim();
      const type = this.editEventType?.value;
      const date = this.editEventDate?.value;
      if (!name || !date) {
        this.showToast('Please provide an event name and date', 'error');
        return;
      }

      const payload = {
        name,
        type,
        date,
        location: this.editEventLocation?.value.trim() || '',
        guests: parseInt(this.editEventGuests?.value, 10) || 100,
        currency: this.editEventCurrency?.value || '₹',
        budget: parseFloat(this.editEventBudget?.value) || 50000,
        duration: this.editEventDuration?.value || '1 Day',
        notes: this.editEventNotes?.value.trim() || ''
      };

      try {
        const res = await fetch(`/api/events/${eventId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          const updated = data.event;
          const idx = this.events.findIndex(e => e.id === eventId);
          if (idx >= 0) this.events[idx] = updated;
          if (this.activeEvent && this.activeEvent.id === eventId) {
            this.activeEvent = updated;
          }
          this.closeModal(this.modalEditEvent);
          this.renderAll();
          this.showToast(`✨ Updated celebration "${updated.name}"!`, 'success');
        } else {
          this.showToast('Failed to update event', 'error');
        }
      } catch (err) {
        console.error('Error updating event:', err);
        this.showToast('Network error while updating event', 'error');
      }
    },

    async handleDeleteEvent(eventId) {
      if (!eventId || eventId === 'undefined' || eventId === 'null') {
        eventId = this.activeEvent ? (this.activeEvent.id || this.activeEvent._id) : null;
      }
      if (!eventId || eventId === 'undefined') {
        this.showToast('No celebration selected to delete.', 'info');
        return;
      }

      const ev = this.events.find(e => (e.id === eventId) || (e._id === eventId));
      const name = ev ? ev.name : 'this celebration';
      if (!confirm(`Are you sure you want to permanently delete "${name}" and all its plans?`)) {
        return;
      }

      try {
        const res = await fetch(`/api/events/${encodeURIComponent(eventId)}`, {
          method: 'DELETE'
        });

        if (res.ok) {
          this.events = this.events.filter(e => (e.id !== eventId) && (e._id !== eventId));
          this.showToast(`Deleted "${name}"`, 'info');
          if (this.activeEvent && ((this.activeEvent.id === eventId) || (this.activeEvent._id === eventId))) {
            if (this.events.length > 0) {
              const nextId = this.events[0].id || this.events[0]._id;
              await this.switchActiveEvent(nextId);
            } else {
              this.activeEvent = null;
            }
          }
          this.renderAll();
        } else {
          this.showToast('Failed to delete event', 'error');
        }
      } catch (err) {
        console.error('Delete event error:', err);
        this.showToast('Error deleting event', 'error');
      }
    },

    /* ==========================================================================
       TAB SWITCHER & MODAL UTILITIES
       ========================================================================== */
    switchTab(tabId) {
      const subPanes = ['overview', 'tasks', 'budget', 'timeline', 'guests', 'vendors', 'notes', 'diary', 'planner'];
      if (subPanes.includes(tabId)) {
        this.switchTab('dashboard');
        this.switchWsPane(tabId === 'planner' ? 'tasks' : tabId);
        return;
      }

      this.activeTab = tabId;
      this.navItems.forEach(item => {
        if (item.getAttribute('data-tab') === tabId) item.classList.add('active');
        else item.classList.remove('active');
      });

      this.tabPanes.forEach(pane => {
        if (pane.id === `tab-${tabId}`) pane.classList.add('active');
        else pane.classList.remove('active');
      });

      const titles = {
        dashboard: 'Dashboard Workspace',
        events: 'My Events Hub',
        copilot: 'Festora AI Copilot',
        settings: 'Settings & Theme'
      };
      if (this.currentSectionTitle) {
        this.currentSectionTitle.textContent = titles[tabId] || 'Workspace';
      }

      this.sidebar.classList.remove('mobile-open');

      if (tabId === 'dashboard') {
        this.switchWsPane(this.currentWsPane || 'overview');
      } else if (tabId === 'events') {
        this.renderMyEvents();
      } else if (tabId === 'copilot') {
        this.updateCopilotContextBanner();
      }
    },

    openModal(modalEl) {
      if (!modalEl) return;
      modalEl.classList.add('show', 'active');
    },

    closeModal(modalEl) {
      if (!modalEl) return;
      modalEl.classList.remove('show', 'active');
    },

    showToast(message, type = 'info') {
      const container = document.getElementById('toastContainer');
      if (!container) return;

      const toast = document.createElement('div');
      toast.className = `toast-pill ${type}`;
      toast.innerHTML = `
        <span class="toast-dot"></span>
        <span class="toast-msg">${this.escapeHtml(message)}</span>
      `;
      container.appendChild(toast);

      setTimeout(() => {
        toast.style.animation = 'toastFadeOut 0.3s forwards';
        setTimeout(() => toast.remove(), 300);
      }, 3500);
    },

    formatMarkdown(text) {
      if (!text) return '';
      let escaped = String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Convert Markdown Headings
      escaped = escaped.replace(/^###\s+(.*$)/gim, '<h4 class="md-h4">$1</h4>');
      escaped = escaped.replace(/^##\s+(.*$)/gim, '<h3 class="md-h3">$1</h3>');
      escaped = escaped.replace(/^#\s+(.*$)/gim, '<h2 class="md-h2">$1</h2>');

      // Bold & Italic
      escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');

      // Convert Bullet lists & Numbered lists
      const lines = escaped.split('\n');
      let inList = false;
      let inNumList = false;
      const processedLines = [];

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const bulletMatch = line.match(/^(\s*)[•\-\*]\s+(.*)$/);
        const numMatch = line.match(/^(\s*)\d+\.\s+(.*)$/);

        if (bulletMatch) {
          if (!inList) {
            if (inNumList) { processedLines.push('</ol>'); inNumList = false; }
            processedLines.push('<ul class="md-list">');
            inList = true;
          }
          processedLines.push(`<li>${bulletMatch[2]}</li>`);
        } else if (numMatch) {
          if (!inNumList) {
            if (inList) { processedLines.push('</ul>'); inList = false; }
            processedLines.push('<ol class="md-num-list">');
            inNumList = true;
          }
          processedLines.push(`<li>${numMatch[2]}</li>`);
        } else {
          if (inList) { processedLines.push('</ul>'); inList = false; }
          if (inNumList) { processedLines.push('</ol>'); inNumList = false; }
          processedLines.push(line);
        }
      }
      if (inList) processedLines.push('</ul>');
      if (inNumList) processedLines.push('</ol>');

      const joined = processedLines.join('\n');
      const paragraphs = joined.split(/\n{2,}/);

      return paragraphs.map(p => {
        const trimmed = p.trim();
        if (!trimmed) return '';
        if (trimmed.startsWith('<h') || trimmed.startsWith('<ul') || trimmed.startsWith('<ol')) {
          return trimmed.replace(/\n/g, '<br>');
        }
        return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
      }).filter(Boolean).join('');
    },

    escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  };

  App.init();
});
