import { buildMonthGrid, monthTitle } from "../../lib/datetime";
import { cx } from "../../lib/utils";

const WEEKDAY_HEADERS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

type CalendarProps = {
  year: number;
  month: number;
  selectedKey: string | null;
  availableDays: Set<string>;
  onMonthChange: (year: number, month: number) => void;
  onSelect: (key: string) => void;
};

export function Calendar({ year, month, selectedKey, availableDays, onMonthChange, onSelect }: CalendarProps) {
  const cells = buildMonthGrid(year, month);

  function shiftMonth(delta: number) {
    const next = new Date(year, month + delta, 1);
    onMonthChange(next.getFullYear(), next.getMonth());
  }

  return (
    <div className="calendar">
      <div className="calendar-header">
        <button type="button" className="calendar-nav" aria-label="Предыдущий месяц" onClick={() => shiftMonth(-1)}>
          ‹
        </button>
        <strong>{monthTitle(year, month)}</strong>
        <button type="button" className="calendar-nav" aria-label="Следующий месяц" onClick={() => shiftMonth(1)}>
          ›
        </button>
      </div>
      <div className="calendar-grid calendar-weekdays">
        {WEEKDAY_HEADERS.map((header) => (
          <span key={header} className="calendar-weekday">
            {header}
          </span>
        ))}
      </div>
      <div className="calendar-grid">
        {cells.map((cell) => {
          const isAvailable = availableDays.has(cell.key);
          return (
            <button
              type="button"
              key={cell.key}
              disabled={!isAvailable}
              onClick={() => onSelect(cell.key)}
              className={cx(
                "calendar-day",
                !cell.inMonth && "outside",
                cell.isToday && "today",
                isAvailable && "available",
                selectedKey === cell.key && "selected",
              )}
            >
              {cell.day}
            </button>
          );
        })}
      </div>
    </div>
  );
}
