import { Plugin } from "@elizaos/core";
import { multiLLMAction } from "./actions.ts";
import { multiLLMProvider } from "./provider.ts";

export const quarmPlugin: Plugin = {
  name: "quarm",
  description: "Quarm plugin",
  actions: [multiLLMAction],
  providers: [multiLLMProvider], // maybe later
  evaluators: [], // maybe later
};
