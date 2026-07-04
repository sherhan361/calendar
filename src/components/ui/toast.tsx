import type { ReactNode } from "react";
import { Toast } from "@base-ui-components/react/toast";

export function ToastProvider({ children }: { children: ReactNode }) {
  return (
    <Toast.Provider>
      {children}
      <ToastRegion />
    </Toast.Provider>
  );
}

function ToastRegion() {
  const { toasts } = Toast.useToastManager();
  return (
    <Toast.Portal>
      <Toast.Viewport className="toast-viewport">
        {toasts.map((toast) => (
          <Toast.Root key={toast.id} toast={toast} className="toast" data-tone={toast.type ?? "info"}>
            <div className="toast-body">
              <Toast.Title className="toast-title" />
              <Toast.Description className="toast-description" />
            </div>
            <Toast.Close className="toast-close" aria-label="Close">
              ×
            </Toast.Close>
          </Toast.Root>
        ))}
      </Toast.Viewport>
    </Toast.Portal>
  );
}

export function useToast() {
  const manager = Toast.useToastManager();
  return {
    success(title: string, description?: string) {
      manager.add({ title, description, type: "success" });
    },
    error(title: string, description?: string) {
      manager.add({ title, description, type: "error", priority: "high" });
    },
    info(title: string, description?: string) {
      manager.add({ title, description, type: "info" });
    },
  };
}
