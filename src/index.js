import { ApolloServer } from 'apollo-server';
import { Neo4jGraphQL } from '@neo4j/graphql';
import { driver } from './db/neo4j.js';

// ----- GraphQL schema -----
const typeDefs = `
  type Movie @node {
    title: String!
    released: Int
  }
`;

// ----- Create Neo4j GraphQL schema -----
const neoSchema = new Neo4jGraphQL({ typeDefs, driver });

// ----- Start the server -----
neoSchema.getSchema().then((schema) => {
  const server = new ApolloServer({ schema });
  server.listen().then(({ url }) => {
    console.log(`🚀 GraphQL API ready at ${url}`);
  });
});
