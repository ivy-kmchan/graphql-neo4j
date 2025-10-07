# graphql-neo4j-project

# data file
1. the root directory contains a copy of the file SavedPlaces.json which is the source file for the neo4j seeder js. You need to place this file into data/GoogleMaps/SavedPlaces.json in your local repo

# Process flow (after first time set up)
1. open the project in VSCode ~/Projects/GraphQL_Neo4j
2. OPTIONAL activate virtual environment: `source .venv/bin/activate`
#note that in my neo4j environment I have deleted the previous DB and created a new instance called travel, then configured the travel instance so it no longer clashes with my other projects
3. in neo4j desktop, find the database for travel, then: 
4. start the instance, make sure it is running, then connect > query
5. EZ-Seed: `npm run seed` populates/updates the `travel` Neo4j database with places from `data/GoogleMaps/SavedPlaces.json`.
5. Apollo for this project defaults to port `4010` so it can run alongside `journal_club`; override with `PORT=xxxx` if needed.
5. EITHER, run index.js to start APOLLO STUDIO: `node scripts/index.js` OR
5. OR, you can also run `npm start` which does the same thing
6. apollo studio has be set to open in firefox as default because it cannot run in safari

## First time setup 
1. Install Node dependencies: `npm install`
2. (Optional) Create a Python virtual environment for the data scripts: `python3 -m venv .venv && source .venv/bin/activate`
3. Install Python tools if you use the notebooks or helpers: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and update the values with your machine's Neo4j connection secrets before starting the API.

## Neo4j config reference
- The folder `neo4j config settings/` contains `neo4j.conf.example`, a copy of the Desktop configuration that matches this project.
- When setting up Neo4j on a new machine, duplicate it to `neo4j.conf`, open Neo4j Desktop → **Manage → Settings** for the `travel` database, and mirror the values from that file. Key overrides compared to the defaults:
  - **Bolt connector**
    - `server.bolt.enabled=true`
    - `server.bolt.listen_address=:7689` (default is `:7687`)
    - `server.bolt.advertised_address=:7689` (default is `:7687`)
  - **HTTP connector**
    - `server.http.enabled=true`
    - `server.http.listen_address=:7476` (default is `:7474`)
    - `server.http.advertised_address=:7476` (default is `:7474`)
- After applying the settings, restart the database so the changes take effect.

1️⃣ Project Initialization
- Create the Git repository (done)
- Initialize a Node.js project (done)

2️⃣ Core Tech Stack
- Neo4j Database – Graph database engine. (done)
- GraphQL API – Query layer. You’ll expose data to clients via a schema. 
- Apollo Server (or Yoga) – To run the GraphQL API.
- neo4j-driver – Official driver to connect Node.js to Neo4j.
- @neo4j/graphql – Auto-generates GraphQL schema and resolvers directly from your Neo4j model.

3️⃣ Recommended Folder Structure (done)

4️⃣ Neo4j Setup 
- Install Neo4j locally (done)
- or run via Docker
- Add credentials to .env: (done)

5️⃣ Minimal Example Code (done)

6️⃣ Next Steps & Learning Path
- Phase 1 > Learn basics > Insert a few nodes/relationships manually (e.g., regions & places). Run simple GraphQL queries and mutations. (done)
- Phase 2 > Schema & relationships > Expand schema with relationships, e.g., location & events relationships.
- Phase 3 > Data ingestion > Write a small script to batch-insert data from a CSV/JSON file.
- Phase 4 > Integration > Build a simple front end (e.g., React) or connect to a tool like Hasura or Apollo Studio for exploration.
- Phase 5 > Advanced features > Add auth (JWT), pagination, filtering, or custom resolvers.

7️⃣ Git & Collaboration Tips
- Commit early and often:
git add . && git commit -m "Set up Apollo server with Neo4j driver" (done)
- Create feature branches when adding new features.
Use GitHub Actions or similar later for CI/CD if you want to deploy.

Your GraphQL + Neo4j stack now has:
- New domain model (Region & Place for travel in Japan)
- Graph data (Hokkaido → Sapporo, Niseko)
- Working GraphQL API returning structured travel data.

Next Steps You Could Take
1. Expand the Graph
- Add more regions and places:
CREATE (k:Region {name: 'Kyoto'});
CREATE (kc:Place {name: 'Kyoto City', type: 'city'});
CREATE (k)-[:HAS_PLACE]->(kc);
- Add details (bestSeason, highlights, etc.).
2. Enhance the Schema
- Add an Activity type and relationships:
type Activity @node {
  name: String!
  category: String
  places: [Place!]! @relationship(type: "AVAILABLE_AT", direction: OUT)
}
3. Build a Front-End
- Create a small web app (React/Next.js) using Apollo Client to display the data.
- Outstanding data action: populate real coordinates for the 91 Japan saved places that exported with `0,0` coordinates (decide on manual lookup vs. Places API enrichment before ingestion).
- Action deferred: 243 non-Japan saves were dropped entirely; re-export if you decide to broaden beyond Japan.
- Follow-up queue: 28 of the zero-coordinate Japan entries describe wide areas (rivers, islands, drives); expect extra effort to pick representative points.
- Quick map preview: serve the repo (`python3 -m http.server 8000`) and open `http://localhost:8000/maps/japan_saved_places.html` to explore the Leaflet map of current JP places. Use a hard refresh after data edits so the browser pulls fresh JSON.
- The map now highlights photo-backed places (green markers) and offers a toggleable blue overlay for unmatched photo locations via `data/photos/place_photo_matches.json`.
- Metadata now includes `properties.category` (`place`/`region`) and `properties.saved_list` (`star`, `heart`, `hotel`, `want_to_go`) so you can mirror Google list types and track custom classifications.

**SavedPlaces Schema Cheatsheet**
- GeoJSON top level: `FeatureCollection` with entries that always use `type: "Feature"` and `geometry.type: "Point"` (Google-supplied, keep untouched for GeoJSON compatibility).
- `geometry.coordinates`: `[longitude, latitude]`; sourced from Google but we may backfill missing values—treat updates as local overrides.
- `properties.date`: ISO 8601 timestamp of when the place was saved in Google (immutable snapshot; do not edit).
- `properties.google_maps_url`: deep link back to the original listing (immutable identifier; do not edit).
- `properties.location`: Google-provided metadata:
  - `name`
  - `address`
  - `country_code`
  (We can correct `name`/`address` locally when Google omits them; `country_code` mirrors the inferred JP tagging script.)
- `properties.category`: **App-added** (`place`/`region` today; extend for seasonal or lodging types later).
- `properties.saved_list`: **App-added** (`star`, `heart`, `hotel`, `want_to_go`; future lists can be appended as we import more Takeout files).
- `properties.prefecture`: **App-added** free text, usually a JP prefecture name for filtering.
- `properties.notes`: **App-added** free-form notes.
- `properties.visited`: **App-added** (`true`/`false`/`null`) to track whether we’ve been there.
- `properties.visited_date`: **App-added** ISO string when we actually visited.
- `properties.tabelog_rating`: **App-added** numeric/string rating for restaurants/hotels (optional).
- `properties.Comment`: Google’s placeholder for zero-coordinate exports (“No location information…”); safe to ignore or strip once coordinates are restored.

Helpers worth rerunning after each Takeout import:
- `python3 scripts/add_initial_categories.py` → ensures every feature has the core metadata keys.
- `python3 scripts/populate_prefectures.py` → derives the prefecture from the address when possible (uses romaji + kanji lookups, only fills blanks unless `--force`).
- `python3 scripts/data_completeness_report.py` → quick snapshot of missing fields.
- `python3 scripts/match_photos_to_places.py` → cross-reference Japan EXIF photos with saved places (adjust `--radius` as needed).
- `python3 scripts/apply_photo_visits.py` → mark places as visited using photo matches (honours existing values unless `--force`).
