import type { ReactNode } from "react";
import { Dialog } from "@base-ui-components/react/dialog";

type ModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
};

export function Modal({ open, onOpenChange, title, description, children, footer }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Backdrop className="dialog-backdrop" />
        <Dialog.Popup className="dialog">
          <div className="dialog-header">
            <Dialog.Title className="dialog-title">{title}</Dialog.Title>
            {description ? <Dialog.Description className="dialog-description">{description}</Dialog.Description> : null}
          </div>
          <div className="dialog-content">{children}</div>
          {footer ? <div className="dialog-footer">{footer}</div> : null}
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export const DialogClose = Dialog.Close;
