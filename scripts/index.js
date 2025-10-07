import { ApolloServer } from 'apollo-server';
import { Neo4jGraphQL } from '@neo4j/graphql';
import neo4j from 'neo4j-driver';
import dotenv from 'dotenv';
import { exec } from 'child_process';

dotenv.config();

const typeDefs = `
  type Region @node {
    name: String!
    places: [Place!]!
      @relationship(type: "HAS_PLACE", direction: OUT)
  }

  type Place @node {
    name: String!
    googleMapsUrl: String!
    type: String
    description: String
    address: String
    latitude: Float
    longitude: Float
    prefecture: String
    savedList: String
    visited: Boolean
    visitedDate: DateTime
    tabelogRating: String
    dateSaved: DateTime
    regions: [Region!]!
      @relationship(type: "HAS_PLACE", direction: IN)
  }
`;

const database = process.env.NEO4J_DATABASE || 'travel';
// Default to a project-specific port so it can run alongside other Apollo servers.
const port = process.env.PORT ? Number(process.env.PORT) : 4010;

const driver = neo4j.driver(
  process.env.NEO4J_URI,
  neo4j.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASSWORD)
);

const sessionConfig = { database };

//const neoSchema = new Neo4jGraphQL({
//  typeDefs,
//  driver,
//  config: {
//    driverConfig: {
//      database,
//    },
//  },
//});

// Updated to match latest Neo4jGraphQL constructor options
const neoSchema = new Neo4jGraphQL({
  typeDefs,
  driver,
  driverConfig: { database },
});

// Opens the server URL in Firefox instead of the system default browser.
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
    // Remove this line (and the openInFirefox helper) to revert to default browser behavior.
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
