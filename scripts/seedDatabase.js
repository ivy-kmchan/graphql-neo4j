import { readFile } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

import neo4j from 'neo4j-driver';

import { driver } from './db/neo4j.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_PATH = path.resolve(__dirname, '../data/GoogleMaps/SavedPlaces.json');
const CHUNK_SIZE = 100;

const upsertPlaceQuery = `
MERGE (place:Place {googleMapsUrl: $googleMapsUrl})
SET
  place.name = $name,
  place.type = $type,
  place.description = $description,
  place.address = $address,
  place.latitude = $latitude,
  place.longitude = $longitude,
  place.prefecture = $prefecture,
  place.savedList = $savedList,
  place.visited = $visited,
  place.visitedDate = $visitedDate,
  place.tabelogRating = $tabelogRating,
  place.dateSaved = $dateSaved
FOREACH (_ IN CASE WHEN $prefecture IS NULL THEN [] ELSE [1] END |
  MERGE (region:Region {name: $prefecture})
  MERGE (region)-[:HAS_PLACE]->(place)
);
`;

const isValidCoordinate = (value) =>
  Array.isArray(value) &&
  value.length === 2 &&
  value.every((item) => typeof item === 'number' && Number.isFinite(item));

const normalizePlace = (feature) => {
  const geometry = feature?.geometry ?? {};
  const properties = feature?.properties ?? {};
  const location = properties.location ?? {};

  if (!location.name) {
    return null;
  }

  const coordinates = geometry.coordinates ?? [];
  const hasCoordinates = isValidCoordinate(coordinates);
  const [longitude, latitude] = hasCoordinates ? coordinates : [null, null];

  const googleMapsUrl = properties.google_maps_url ?? null;
  if (!googleMapsUrl) {
    return null;
  }

  const prefecture = properties.prefecture || null;
  const category = properties.category || 'place';
  const notes = properties.notes || null;

  return {
    googleMapsUrl,
    name: location.name,
    description: notes ?? location.address ?? null,
    address: location.address ?? null,
    type: category,
    latitude,
    longitude,
    savedList: properties.saved_list ?? null,
    visited: properties.visited ?? null,
    visitedDate: properties.visited_date ?? null,
    tabelogRating: properties.tabelog_rating ?? null,
    dateSaved: properties.date ?? null,
    prefecture,
  };
};

const chunk = (collection, size) => {
  const result = [];
  for (let index = 0; index < collection.length; index += size) {
    result.push(collection.slice(index, index + size));
  }
  return result;
};

async function ensureConstraints(session) {
  const statements = [
    'CREATE CONSTRAINT IF NOT EXISTS FOR (p:Place) REQUIRE p.googleMapsUrl IS UNIQUE',
    'CREATE CONSTRAINT IF NOT EXISTS FOR (r:Region) REQUIRE r.name IS UNIQUE',
  ];

  for (const statement of statements) {
    await session.run(statement);
  }
}

async function upsertPlaces(session, places) {
  const batches = chunk(places, CHUNK_SIZE);

  for (const [index, batch] of batches.entries()) {
    await session.executeWrite(async (tx) => {
      for (const place of batch) {
        await tx.run(upsertPlaceQuery, place);
      }
    });
    console.log(`Inserted batch ${index + 1}/${batches.length}`);
  }
}

async function main() {
  console.log('Loading saved places data from', DATA_PATH);
  const raw = await readFile(DATA_PATH, 'utf-8');
  const payload = JSON.parse(raw);
  const features = Array.isArray(payload.features) ? payload.features : [];

  const normalized = features
    .map(normalizePlace)
    .filter((value) => value !== null);

  if (!normalized.length) {
    console.warn('No places to import. Exiting.');
    return;
  }

  const session = driver.session({ defaultAccessMode: neo4j.session.WRITE });

  try {
    console.log(`Preparing constraints...`);
    await ensureConstraints(session);
    console.log(`Seeding ${normalized.length} places...`);
    await upsertPlaces(session, normalized);
    console.log('Seeding completed successfully.');
  } finally {
    await session.close();
    await driver.close();
  }
}

main().catch((error) => {
  console.error('Seeding failed:', error);
  process.exitCode = 1;
});
