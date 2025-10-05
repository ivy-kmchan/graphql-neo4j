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
    type: String
    description: String
    regions: [Region!]!
      @relationship(type: "HAS_PLACE", direction: IN)
  }
`;

const driver = neo4j.driver(
  process.env.NEO4J_URI,
  neo4j.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASSWORD)
);

const neoSchema = new Neo4jGraphQL({
  typeDefs,
  driver,
  config: {
    database: process.env.NEO4J_DATABASE,
  },
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

console.log('Connecting to', process.env.NEO4J_URI, '→ DB:', process.env.NEO4J_DATABASE);

neoSchema
  .getSchema()
  .then((schema) => {
    const server = new ApolloServer({ schema });
    server.listen().then(({ url }) => {
      console.log(`🚀 GraphQL API ready at ${url}`);
      // Remove this line (and the openInFirefox helper) to revert to default browser behavior.
      openInFirefox(url);
    });
  })
  .catch((err) => {
    console.error('Schema generation failed:', err);
  });
