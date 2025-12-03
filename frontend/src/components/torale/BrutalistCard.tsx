import React from 'react';
import { motion, MotionProps } from '@/lib/motion-compat';
import { cn } from '@/lib/utils';

/**
 * BrutalistCard - Neo-brutalist card wrapper with consistent styling
 *
 * Variants:
 * - default: White background, 2px border
 * - clickable: Adds cursor pointer, hover effects
 * - ghost: Transparent background
 */

interface BrutalistCardProps extends Omit<MotionProps, 'onClick'> {
  children: React.ReactNode;
  variant?: 'default' | 'clickable' | 'ghost';
  onClick?: () => void;
  className?: string;
  animate?: boolean; // Enable motion animations
  hoverEffect?: boolean; // Enable hover lift effect
}

export const BrutalistCard: React.FC<BrutalistCardProps> = ({
  children,
  variant = 'default',
  onClick,
  className,
  animate = false,
  hoverEffect = false,
  ...motionProps
}) => {
  const baseStyles = 'relative flex flex-col';

  const variantStyles = {
    default: 'bg-white border-2 border-zinc-200',
    clickable:
      'bg-white border-2 border-zinc-200 cursor-pointer transition-all hover:border-zinc-900 hover:shadow-brutalist',
    ghost: 'bg-transparent',
  };

  const cardContent = (
    <div
      className={cn(
        baseStyles,
        variantStyles[variant],
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );

  if (animate || hoverEffect) {
    const animationProps = {
      ...(animate && {
        layout: true,
        initial: { opacity: 0, y: 10 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, scale: 0.95 },
      }),
      ...(hoverEffect && {
        whileHover: { y: -2, boxShadow: '0 10px 30px -10px rgba(0,0,0,0.1)' },
      }),
    };

    return (
      <motion.div
        className={cn(
          baseStyles,
          variantStyles[variant],
          onClick && 'cursor-pointer',
          className
        )}
        onClick={onClick}
        {...animationProps}
        {...motionProps}
      >
        {children}
      </motion.div>
    );
  }

  return cardContent;
};
