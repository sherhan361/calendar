import type { BookingStatus, ConfirmationPolicyType, Weekday } from "./types";

export const t = {
  brand: "Cal.com",
  nav: {
    eventTypes: "Типы событий",
    bookings: "Бронирования",
    availability: "Доступность",
  },
  common: {
    create: "Создать",
    search: "Искать",
    cancel: "Отмена",
    clear: "Очистить",
    save: "Сохранить",
    back: "Назад",
    refresh: "Обновить",
    logout: "Выйти",
    syncing: "Синхронизация…",
    filter: "Фильтр",
    copyLink: "Скопировать ссылку",
    openPage: "Открыть страницу",
    privateLink: "Приватная ссылка",
    more: "Ещё",
    hidden: "Скрытый",
    default: "По умолчанию",
    noDescription: "Без описания",
  },
  login: {
    eyebrow: "Рабочее пространство",
    title: "Войдите, чтобы управлять встречами",
    hint: "Демо-учётные данные уже заполнены из базы.",
    email: "Email",
    password: "Пароль",
    submit: "Войти",
    submitting: "Вход…",
  },
  eventTypes: {
    title: "Типы событий",
    subtitle: "Создайте мероприятие, чтобы поделиться с людьми для бронирования в вашем календаре.",
    empty: "Пока нет типов событий. Создайте первую ссылку для бронирования.",
    createTitle: "Создать тип события",
    createSubtitle: "Ссылка для бронирования на основе вашей доступности.",
    fieldTitle: "Название",
    fieldSlug: "Slug",
    fieldDuration: "Длительность (мин)",
    fieldConfirmation: "Подтверждение",
    fieldDescription: "Описание",
    createSubmit: "Создать",
    creating: "Создание…",
    linkCopied: "Ссылка скопирована",
    privateLinkCopied: "Приватная ссылка скопирована",
    created: "Тип события создан",
    createError: "Не удалось создать тип события",
    linkError: "Не удалось создать ссылку",
    toggleError: "Не удалось изменить видимость",
  },
  availability: {
    title: "Доступность",
    subtitle: "Измените временные интервалы, доступные для бронирования.",
    myAvailability: "Моя доступность",
    teamAvailability: "Доступность команды",
    workingHours: "Часы работы",
    empty: "Расписание не найдено. Создайте или загрузите seed-данные.",
    edit: "Редактировать",
    addInterval: "Добавить интервал",
    remove: "Удалить",
    save: "Сохранить доступность",
    saving: "Сохранение…",
    saved: "Доступность сохранена",
    saveError: "Не удалось сохранить",
    awayHint: "Временно отсутствуете?",
    awayAction: "Добавить перенаправление",
  },
  bookings: {
    title: "Бронирования",
    tabs: {
      upcoming: "Предстоящие",
      unconfirmed: "Не подтверждено",
      past: "Прошлые",
      cancelled: "Отменено",
    },
    emptyUpcoming: "Нет бронирований со статусом «предстоящие»",
    emptyUpcomingHint:
      "У вас нет предстоящих бронирований. Как только кто-то забронирует встречу с вами, она будет отображена здесь.",
    emptyUnconfirmed: "Нет неподтверждённых бронирований",
    emptyUnconfirmedHint: "Запросы, ожидающие вашего подтверждения, появятся здесь.",
    emptyPast: "Нет прошлых бронирований",
    emptyPastHint: "Завершённые встречи будут отображаться здесь.",
    emptyCancelled: "Нет отменённых бронирований",
    emptyCancelledHint: "Отменённые и отклонённые встречи будут здесь.",
    confirm: "Подтвердить",
    decline: "Отклонить",
    cancelBooking: "Отменить",
    filterFrom: "С даты",
    filterTo: "По дату",
    filterError: "Не удалось применить фильтр",
    declineTitle: "Отклонить бронирование",
    cancelTitle: "Отменить бронирование",
    keepBooking: "Оставить бронирование",
    reasonLabel: "Причина (необязательно)",
    reasonPlaceholder: "Будет отправлено гостю",
    confirmed: "Бронирование подтверждено",
    declined: "Бронирование отклонено",
    cancelled: "Бронирование отменено",
    actionError: "Не удалось выполнить действие",
    confirmError: "Не удалось подтвердить",
  },
  public: {
    loading: "Загрузка страницы бронирования…",
    timeZone: "Часовой пояс",
    selectDay: "Выберите день",
    pickTime: "Выберите время",
    noSlots: "Нет доступного времени. Попробуйте другой день.",
    name: "Имя",
    email: "Email",
    confirmBooking: "Подтвердить бронирование",
    booking: "Бронирование…",
    slotTaken: "Это время уже заняли. Выберите другой доступный слот.",
    confirmed: "Ваша встреча подтверждена",
    requestSent: "Запрос отправлен",
    pendingHint: "Организатор рассмотрит запрос и подтвердит встречу.",
    backHome: "На главную",
    minutes: "мин",
  },
} as const;

export function confirmationPolicyLabel(type: ConfirmationPolicyType) {
  switch (type) {
    case "automatic":
      return "Автоматически";
    case "host":
      return "Организатор";
    case "attendee":
      return "Участник";
    default: {
      const _exhaustive: never = type;
      return _exhaustive;
    }
  }
}

export function bookingStatusLabel(status: BookingStatus) {
  switch (status) {
    case "pending_host":
      return "Ожидает организатора";
    case "pending_attendee":
      return "Ожидает участника";
    case "confirmed":
      return "Подтверждено";
    case "declined":
      return "Отклонено";
    case "cancelled":
      return "Отменено";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

const weekdayRu: Record<Weekday, string> = {
  monday: "пн",
  tuesday: "вт",
  wednesday: "ср",
  thursday: "чт",
  friday: "пт",
  saturday: "сб",
  sunday: "вс",
};

export function formatAvailabilitySummary(days: Weekday[], startTime: string, endTime: string) {
  const dayPart = days.map((day) => weekdayRu[day]).join(", ");
  return `${dayPart}, ${formatTimeRu(startTime)} – ${formatTimeRu(endTime)}`;
}

function formatTimeRu(time: string) {
  const [hour, minute] = time.split(":").map(Number);
  const date = new Date(2000, 0, 1, hour, minute);
  return new Intl.DateTimeFormat("ru-RU", { hour: "numeric", minute: "2-digit" }).format(date);
}

export const policyOptions = [
  { value: "automatic" as const, label: "Автоматически" },
  { value: "host" as const, label: "Организатор" },
  { value: "attendee" as const, label: "Участник" },
];
