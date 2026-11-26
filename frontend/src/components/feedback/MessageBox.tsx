import styles from "./Feedback.module.css";

interface MessageBoxProps {
  title: string;
  message: string;
  /** "empty" for nothing-found states, "error" for failures. */
  variant?: "empty" | "error";
  actionLabel?: string;
  onAction?: () => void;
}

/**
 * Shared box for empty and error states (mockups S3 and S6).
 */
export function MessageBox({
  title,
  message,
  variant = "empty",
  actionLabel,
  onAction,
}: MessageBoxProps) {
  const isError = variant === "error";
  return (
    <div
      className={`${styles.box} ${isError ? styles.boxError : ""}`}
      role={isError ? "alert" : "status"}
    >
      <p className={styles.title}>! {title}</p>
      <p className={styles.message}>{message}</p>
      {actionLabel && onAction && (
        <button type="button" className={styles.button} onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}
