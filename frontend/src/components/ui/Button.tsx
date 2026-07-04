import { forwardRef } from "react";
import type { ButtonHTMLAttributes } from "react";
import { cx } from "../../lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "md" | "sm";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", size = "md", className, type = "button", ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cx("btn", `btn-${variant}`, size === "sm" && "btn-sm", className)}
      {...rest}
    />
  );
});

export function buttonClass(variant: Variant = "secondary", size: Size = "md") {
  return cx("btn", `btn-${variant}`, size === "sm" && "btn-sm");
}
