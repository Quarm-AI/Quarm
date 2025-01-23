import { PostgresDatabaseAdapter } from "@elizaos/adapter-postgres";
import RedisClient from "@elizaos/adapter-redis";
import { createNodePlugin } from "@elizaos/plugin-node";
import path from "node:path";
import fs from "node:fs";
import {
  validateCharacterConfig,
  type Character,
  AgentRuntime,
  ModelProviderName,
  DbCacheAdapter,
  elizaLogger,
  CacheManager,
} from "@ai16z/eliza";

import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);

const __dirname = path.dirname(__filename);

const nodePlugin = createNodePlugin();

const postgresAdapter = new PostgresDatabaseAdapter({
  host: process.env.POSTGRES_HOST,
  port: process.env.POSTGRES_PORT,
  database: process.env.POSTGRES_DATABASE,
  username: process.env.POSTGRES_USERNAME,
  password: process.env.POSTGRES_PASSWORD,
});

function tryLoadFile(filePath: string): string | null {
  try {
    return fs.readFileSync(filePath, "utf8");
  } catch (e) {
    return null;
  }
}

function mergeCharacters(base: Character, child: Character): Character {
  const mergeObjects = (baseObj: any, childObj: any) => {
    const result: any = {};
    const keys = new Set([
      ...Object.keys(baseObj || {}),
      ...Object.keys(childObj || {}),
    ]);
    keys.forEach((key) => {
      if (
        typeof baseObj[key] === "object" &&
        typeof childObj[key] === "object" &&
        !Array.isArray(baseObj[key]) &&
        !Array.isArray(childObj[key])
      ) {
        result[key] = mergeObjects(baseObj[key], childObj[key]);
      } else if (Array.isArray(baseObj[key]) || Array.isArray(childObj[key])) {
        result[key] = [...(baseObj[key] || []), ...(childObj[key] || [])];
      } else {
        result[key] =
          childObj[key] !== undefined ? childObj[key] : baseObj[key];
      }
    });
    return result;
  };
  return mergeObjects(base, child);
}

async function handlePluginImporting(plugins: string[]) {
  if (plugins.length > 0) {
    elizaLogger.info("Plugins are: ", plugins);
    const importedPlugins = await Promise.all(
      plugins.map(async (plugin) => {
        try {
          const importedPlugin = await import(plugin);
          const functionName =
            plugin
              .replace("@elizaos/plugin-", "")
              .replace(/-./g, (x) => x[1].toUpperCase()) + "Plugin"; // Assumes plugin function is camelCased with Plugin suffix
          return importedPlugin.default || importedPlugin[functionName];
        } catch (importError) {
          elizaLogger.error(`Failed to import plugin: ${plugin}`, importError);
          return []; // Return null for failed imports
        }
      }),
    );
    return importedPlugins;
  } else {
    return [];
  }
}

async function loadCharacter(filePath: string): Promise<Character> {
  const content = tryLoadFile(filePath);
  if (!content) {
    throw new Error(`Character file not found: ${filePath}`);
  }
  let character = JSON.parse(content);
  validateCharacterConfig(character);

  // .id isn't really valid
  const characterId = character.id || character.name;
  const characterPrefix = `CHARACTER.${characterId.toUpperCase().replace(/ /g, "_")}.`;
  const characterSettings = Object.entries(process.env)
    .filter(([key]) => key.startsWith(characterPrefix))
    .reduce((settings, [key, value]) => {
      const settingKey = key.slice(characterPrefix.length);
      return { ...settings, [settingKey]: value };
    }, {});
  if (Object.keys(characterSettings).length > 0) {
    character.settings = character.settings || {};
    character.settings.secrets = {
      ...characterSettings,
      ...character.settings.secrets,
    };
  }
  // Handle plugins
  character.plugins = await handlePluginImporting(character.plugins);
  if (character.extends) {
    elizaLogger.info(
      `Merging  ${character.name} character with parent characters`,
    );
    for (const extendPath of character.extends) {
      const baseCharacter = await loadCharacter(
        path.resolve(path.dirname(filePath), extendPath),
      );
      character = mergeCharacters(baseCharacter, character);
      elizaLogger.info(`Merged ${character.name} with ${baseCharacter.name}`);
    }
  }
  return character;
}

function initializeCache(character: Character) {
  if (process.env.REDIS_URL) {
    elizaLogger.info("Connecting to Redis...");
    const redisClient = new RedisClient(process.env.REDIS_URL);
    if (!character?.id) {
      throw new Error(
        "CacheStore.REDIS requires id to be set in character definition",
      );
    }
    return new CacheManager(new DbCacheAdapter(redisClient, character.id));
  } else {
    throw new Error("REDIS_URL environment variable is not set.");
  }
}

const character = await loadCharacter(
  path.resolve(__dirname, "../characters/trump.character.json"),
);

const agent = new AgentRuntime({
  modelProvider: ModelProviderName.OPENAI,
  token: process.env.OPENAI_API_KEY || "",
  databaseAdapter: postgresAdapter,
  character,
  cacheManager: initializeCache(character),
  // plugins: [nodePlugin as any],
});
