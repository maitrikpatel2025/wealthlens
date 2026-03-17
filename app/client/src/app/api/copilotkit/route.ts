import { HttpAgent } from "@ag-ui/client";

import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  OpenAIAdapter,
} from "@copilotkit/runtime";

import { NextRequest } from "next/server";

const serviceAdapter = new OpenAIAdapter();

const wealthlens = new HttpAgent({
  url: "http://127.0.0.1:8000/wealthlens-agent",
});

const runtime = new CopilotRuntime({
  agents: {
    wealthlens,
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
