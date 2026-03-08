/**
 * Error Message Component
 * Displays error messages with optional retry button
 * Supports Hindi and English messages
 */

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  type?: 'error' | 'warning' | 'info';
}

export function ErrorMessage({ message, onRetry, type = 'error' }: ErrorMessageProps) {
  const bgColors = {
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200',
    info: 'bg-blue-50 border-blue-200',
  };

  const textColors = {
    error: 'text-red-800',
    warning: 'text-yellow-800',
    info: 'text-blue-800',
  };

  const buttonColors = {
    error: 'text-red-600 hover:text-red-800',
    warning: 'text-yellow-600 hover:text-yellow-800',
    info: 'text-blue-600 hover:text-blue-800',
  };

  return (
    <div className={`${bgColors[type]} border rounded-lg p-4`} role="alert">
      <p className={textColors[type]}>{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className={`mt-2 ${buttonColors[type]} underline focus:outline-none focus:ring-2 focus:ring-offset-2`}
        >
          पुनः प्रयास करें (Retry)
        </button>
      )}
    </div>
  );
}

export default ErrorMessage;
