import React from 'react';

/**
 * Butterfly Icon Component
 * Precision-crafted vector butterfly designed to match the 24x24 Lucide icon grid,
 * stroke width, rounded terminal caps, and color theming.
 */
export default function Butterfly({
  size = 20,
  color = 'currentColor',
  className = '',
  style = {},
  ...props
}) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`lucide-butterfly ${className}`}
      style={{
        display: 'inline-block',
        verticalAlign: 'middle',
        flexShrink: 0,
        ...style
      }}
      aria-hidden="true"
      {...props}
    >
      {/* Butterfly Center Body */}
      <path d="M12 7.5v9" />

      {/* Antennae */}
      <path d="M12 7.5c-0.8-2.2-2.5-3.5-4-3" />
      <path d="M12 7.5c0.8-2.2 2.5-3.5 4-3" />

      {/* Forewings (Upper Wings) */}
      <path d="M12 8.5c-2.5-4.5-9-4-9.8 1.5c-0.6 4.2 3.8 5.5 9.8 3.5" />
      <path d="M12 8.5c2.5-4.5 9-4 9.8 1.5c0.6 4.2-3.8 5.5-9.8 3.5" />

      {/* Hindwings (Lower Wings) */}
      <path d="M12 13.5c-4.2 0.5-7.2 3.2-5.2 6.2c1.8 2.2 4.8-0.8 5.2-3.2" />
      <path d="M12 13.5c4.2 0.5 7.2 3.2 5.2 6.2c-1.8 2.2-4.8-0.8-5.2-3.2" />
    </svg>
  );
}
