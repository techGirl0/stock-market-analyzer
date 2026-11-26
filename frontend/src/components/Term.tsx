import { useId } from "react";
import styles from "./Term.module.css";

interface TermProps {
  children: React.ReactNode;
  /** Short plain-language explanation, shown on hover or keyboard focus. */
  explanation: string;
}

/**
 * A word with a dotted underline that explains itself on hover or focus.
 * Works with keyboard and screen readers (the explanation is the description).
 */
export function Term({ children, explanation }: TermProps) {
  const id = useId();
  return (
    <span className={styles.term} tabIndex={0} aria-describedby={id}>
      {children}
      <span role="tooltip" id={id} className={styles.tooltip}>
        {explanation}
      </span>
    </span>
  );
}
