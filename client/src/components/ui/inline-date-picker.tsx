"use client"

import * as React from "react"
import { format } from "date-fns"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { cn } from "@/lib/utils"

interface InlineDatePickerProps {
  date?: Date
  setDate: (date?: Date) => void
  placeholder?: string
  disabled?: boolean
  minDate?: Date
  maxDate?: Date
  className?: string
}

export function InlineDatePicker({
  date,
  setDate,
  placeholder = "Pick a date",
  disabled = false,
  minDate,
  maxDate,
  className,
}: InlineDatePickerProps) {
  const [showCalendar, setShowCalendar] = React.useState(false)

  const handleSelect = (selectedDate: Date | undefined) => {
    setDate(selectedDate)
    // Keep calendar open for a better user experience
  }

  const handleButtonClick = () => {
    setShowCalendar(!showCalendar)
  }

  return (
    <div className={cn("space-y-2", className)}>
      <Button
        type="button"
        variant={"outline"}
        onClick={handleButtonClick}
        className={cn(
          "w-full justify-start text-left font-normal",
          !date && "text-muted-foreground"
        )}
        disabled={disabled}
      >
        {date ? format(date, "EEE, MMM d, yyyy") : <span>{placeholder}</span>}
      </Button>
      
      {showCalendar && (
        <div className="mt-1 bg-background border rounded-md p-2 shadow-md relative z-50">
          <Calendar
            mode="single"
            selected={date}
            onSelect={handleSelect}
            disabled={(day) => {
              if (minDate && day < minDate) {
                return true
              }
              if (maxDate && day > maxDate) {
                return true
              }
              return false
            }}
            initialFocus
            className="rounded-md"
          />
          <div className="mt-2 flex justify-end">
            <Button 
              variant="default" 
              size="sm" 
              onClick={() => setShowCalendar(false)}
              className="bg-primary text-primary-foreground"
            >
              Done
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}