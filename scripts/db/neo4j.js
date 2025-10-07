//import dotenv from 'dotenv';
//dotenv.config();   // ✅ must come first
//console.log("Loaded NEO4J_URI =", process.env.NEO4J_URI);
//
//import neo4j from 'neo4j-driver';
//
//export const driver = neo4j.driver(
//  process.env.NEO4J_URI,
//  neo4j.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASSWORD)
//);

// updated to use NEO4J_DATABASE env var or default to 'travel'
import neo4j from 'neo4j-driver';
import dotenv from 'dotenv';

dotenv.config();

export const driver = neo4j.driver(
  process.env.NEO4J_URI,
  neo4j.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASSWORD)
);

export const database = process.env.NEO4J_DATABASE || 'travel';

export const getSession = (mode = neo4j.session.WRITE) =>
  driver.session({
    defaultAccessMode: mode,
    database,
  });