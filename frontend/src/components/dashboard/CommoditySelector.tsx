"use client"

import * as React from "react"
import { Check, ChevronsUpDown } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

const commodities = [
  {
    value: "onion",
    label: "Onion (Red)",
    id: 1,
  },
  {
    value: "potato",
    label: "Potato (Jyoti)",
    id: 2,
  },
  {
    value: "tomato",
    label: "Tomato (Hybrid)",
    id: 3,
  },
  {
    value: "wheat",
    label: "Wheat (Sharbati)",
    id: 4,
  },
  {
    value: "rice",
    label: "Rice (Basmati)",
    id: 5,
  },
]

interface CommoditySelectorProps {
  onSelect?: (id: number) => void
}

export function CommoditySelector({ onSelect }: CommoditySelectorProps) {
  const [open, setOpen] = React.useState(false)
  const [value, setValue] = React.useState("potato")

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {value
            ? commodities.find((commodity) => commodity.value === value)?.label
            : "Select commodity..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder="Search commodity..." />
          <CommandList>
            <CommandEmpty>No commodity found.</CommandEmpty>
            <CommandGroup>
              {commodities.map((commodity) => (
                <CommandItem
                    key={commodity.value}
                    value={commodity.value}
                    onSelect={(currentValue) => {
                      const selected = commodities.find(c => c.value === currentValue)
                      setValue(currentValue === value ? "" : currentValue)
                      setOpen(false)
                      if (selected && onSelect) {
                        onSelect(selected.id)
                      }
                    }}
                >
                    <Check
                    className={cn(
                        "mr-2 h-4 w-4",
                        value === commodity.value ? "opacity-100" : "opacity-0"
                    )}
                    />
                    {commodity.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
