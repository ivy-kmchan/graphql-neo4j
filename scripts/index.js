import { ApolloServer } from 'apollo-server';
import { Neo4jGraphQL } from '@neo4j/graphql';
import neo4j from 'neo4j-driver';
import dotenv from 'dotenv';
import { exec } from 'child_process';

dotenv.config();

const typeDefs = `
  type Query {
    placesCount: Int!
  }

  type Region @node {
    name: String!
    places: [Place!]!
      @relationship(type: "HAS_PLACE", direction: OUT)
  }

  type ActivityCategory @node {
    name: String!
    description: String
    places: [Place!]!
      @relationship(type: "HAS_ACTIVITY", direction: IN)
  }

  type CuisineType @node {
    name: String!
    description: String
    places: [Place!]!
      @relationship(type: "SERVES_CUISINE", direction: IN)
  }

  type TransportType @node {
    name: String!
    description: String
  }

  type Place @node {
    name: String!
    google_maps_url: String
    type: String
    description: String
    address: String
    latitude: Float
    longitude: Float
    prefecture: String
    saved_list: String
    visited: Boolean
    category: String
    activity_type: String
    date: String
    regions: [Region!]!
      @relationship(type: "HAS_PLACE", direction: IN)
    activities: [ActivityCategory!]!
      @relationship(type: "HAS_ACTIVITY", direction: OUT)
    cuisines: [CuisineType!]!
      @relationship(type: "SERVES_CUISINE", direction: OUT)
  }
`;

const database = process.env.NEO4J_DATABASE || 'travel';
const port = process.env.PORT ? Number(process.env.PORT) : 4010;

const driver = neo4j.driver(
  process.env.NEO4J_URI,
  neo4j.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASSWORD)
);

const sessionConfig = { database };

// ✅ Integrate the custom resolver directly in the Neo4jGraphQL schema
const neoSchema = new Neo4jGraphQL({
  typeDefs,
  driver,
  driverConfig: { database },
  resolvers: {
    Query: {
      placesCount: async () => {
        console.log('placesCount resolver called');
        const session = driver.session({ database });
        try {
          const result = await session.run('MATCH (p:Place) RETURN count(p) as count');
          const count = result.records[0]?.get('count')?.toNumber?.() ?? 0;
          console.log('placesCount →', count);
          return count;
        } catch (error) {
          console.error('Error in placesCount resolver:', error);
          return 0;
        } finally {
          await session.close();
        }
      },
    },
  },
});

// Opens the server URL in Firefox instead of the default browser
const openInFirefox = (url) => {
  let command;
  if (process.platform === 'darwin') {
    command = `open -a "Firefox" "${url}"`;
  } else if (process.platform === 'win32') {
    command = `start "" firefox "${url}"`;
  } else {
    command = `firefox "${url}"`;
  }

  exec(command, { shell: true }, (error) => {
    if (error) {
      console.error('Failed to open Firefox:', error);
    }
  });
};

console.log('Connecting to', process.env.NEO4J_URI, '→ DB:', database);

const startServer = async () => {
  try {
    const schema = await neoSchema.getSchema();

    const server = new ApolloServer({
      schema,
      context: ({ req }) => ({
        req,
        driver,
        sessionConfig,
      }),
    });

    const { url } = await server.listen({ port });
    console.log(`🚀 GraphQL API ready at ${url} (DB: ${database})`);
    openInFirefox(url);

    const shutdown = async () => {
      console.log('Shutting down Apollo Server...');
      await server.stop();
      await driver.close();
      process.exit(0);
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  } catch (error) {
    console.error('Schema generation failed:', error);
    await driver.close();
    process.exit(1);
  }
};

startServer();
