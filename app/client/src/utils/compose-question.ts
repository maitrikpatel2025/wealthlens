import type { WidgetSpec } from "@/types/widgets";

/** Map widget type to a natural-language question for the agent. */
export function composeWidgetQuestion(widget: WidgetSpec): string {
  const title = widget.title;
  switch (widget.type) {
    case "pie":
      return `Drill deeper into the "${title}" breakdown. What stands out and what are the risks?`;
    case "bar":
      return `Analyze the data in "${title}". Which items are notable and why?`;
    case "table":
      return `Review the "${title}" table. Highlight any concerns or opportunities.`;
    case "gauge":
      return `Explain the "${title}" score. Is this healthy and what could improve it?`;
    case "summary":
      return `Walk me through the "${title}" metrics. What should I pay attention to?`;
    case "line":
      return `Analyze the trend in "${title}". How has this changed over time?`;
    case "treemap":
      return `Break down the "${title}" treemap. Where is the concentration?`;
    case "sankey":
      return `Explain the flow shown in "${title}". Where is the money going?`;
    default:
      return `Tell me more about "${title}".`;
  }
}

/** Build a drill-down question when the user clicks a specific data point. */
export function composeDataPointQuestion(
  widget: WidgetSpec,
  dataPoint: Record<string, any>,
): string {
  const title = widget.title;

  switch (widget.type) {
    case "pie": {
      const name = dataPoint.name || dataPoint.label || "this slice";
      const value = dataPoint.value;
      return `In "${title}", "${name}" represents ${value != null ? value + "%" : "a portion"}. Break down what's inside "${name}" and whether it's appropriate.`;
    }
    case "bar": {
      const label = dataPoint.label || dataPoint.name || "this bar";
      const value = dataPoint.value;
      return `In "${title}", "${label}" shows a value of ${value ?? "N/A"}. Why is it at this level and how does it compare?`;
    }
    case "table": {
      const symbol = dataPoint.symbol || dataPoint.name || dataPoint.label;
      if (symbol) {
        return `Tell me more about ${symbol} from the "${title}" table. What should I know about this holding?`;
      }
      const firstVal = Object.values(dataPoint)[0];
      return `Analyze the row "${firstVal}" from "${title}". What's notable?`;
    }
    default: {
      const label = dataPoint.name || dataPoint.label || JSON.stringify(dataPoint).slice(0, 60);
      return `Drill into "${label}" from "${title}".`;
    }
  }
}
