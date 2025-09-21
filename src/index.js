import { ApolloServer } from 'apollo-server';
import { Neo4jGraphQL } from '@neo4j/graphql';
import neo4j from 'neo4j-driver';
import dotenv from 'dotenv';

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
    regions: [Region!]! @relationship(type: "HAS_PLACE", direction: IN)
  }
`;

const driver = neo4j.driver(
  process.env.NEO4J_URI,
  neo4j.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASSWORD)
);

const neoSchema = new Neo4jGraphQL({ typeDefs, driver });

neoSchema.getSchema()
  .then((schema) => {
    const server = new ApolloServer({ schema });
    server.listen().then(({ url }) => {
      console.log(`🚀 GraphQL API ready at ${url}`);
    });
  })
  .catch((err) => {
    console.error('Schema generation failed:', err);
  });
