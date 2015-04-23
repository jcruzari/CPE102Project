import entities
import worldmodel
import pygame
import math
import random
import point
import image_store

BLOB_RATE_SCALE = 4
BLOB_ANIMATION_RATE_SCALE = 50
BLOB_ANIMATION_MIN = 1
BLOB_ANIMATION_MAX = 3

ORE_CORRUPT_MIN = 20000
ORE_CORRUPT_MAX = 30000

QUAKE_STEPS = 10
QUAKE_DURATION = 1100
QUAKE_ANIMATION_RATE = 100

VEIN_SPAWN_DELAY = 500
VEIN_RATE_MIN = 8000
VEIN_RATE_MAX = 17000


def sign(x):
   if x < 0:
      return -1
   elif x > 0:
      return 1
   else:
      return 0


def adjacent(pt1, pt2):
   return ((pt1.x == pt2.x and abs(pt1.y - pt2.y) == 1) or
      (pt1.y == pt2.y and abs(pt1.x - pt2.x) == 1))

def try_transform_miner_full(world, entity):
   new_entity = entities.MinerNotFull(
      entity.get_name(), entity.get_resource_limit(),
      entity.get_position(), entity.get_rate(),
      entity.get_images(), entity.get_animation_rate())

   return new_entity


def try_transform_miner_not_full(world, entity):
   if entity.resource_count < entity.resource_limit:
      return entity
   else:
      new_entity = entities.MinerFull(
         entity.get_name(), entity.get_resource_limit(),
         entity.get_position(), entity.get_rate(),
         entity.get_images(), entity.get_animation_rate())
      return new_entity

def remove_entity(world, entity):
   for action in entity.get_pending_actions():
      world.unschedule_action(action)
   entity.clear_pending_actions()
   world.remove_entity(entity)


def create_blob(world, name, pt, rate, ticks, i_store):
   blob = entities.OreBlob(name, pt, rate,
      image_store.get_images(i_store, 'blob'),
      random.randint(BLOB_ANIMATION_MIN, BLOB_ANIMATION_MAX)
      * BLOB_ANIMATION_RATE_SCALE)
   schedule_blob(world, blob, ticks, i_store)
   return blob


def schedule_blob(world, blob, ticks, i_store):
   schedule_action(world, blob, world.create_ore_blob_action(blob, i_store),
      ticks + blob.get_rate())
   schedule_animation(world, blob)


def schedule_miner(world, miner, ticks, i_store):
   schedule_action(world, miner, world.create_miner_action(miner, i_store),
      ticks + miner.get_rate())
   schedule_animation(world, miner)


def create_ore(world, name, pt, ticks, i_store):
   ore = entities.Ore(name, pt, image_store.get_images(i_store, 'ore'),
      random.randint(ORE_CORRUPT_MIN, ORE_CORRUPT_MAX))
   schedule_ore(world, ore, ticks, i_store)

   return ore


def schedule_ore(world, ore, ticks, i_store):
   schedule_action(world, ore,
      world.create_ore_transform_action(ore, i_store),
      ticks + ore.get_rate())


def create_quake(world, pt, ticks, i_store):
   quake = entities.Quake("quake", pt,
      image_store.get_images(i_store, 'quake'), QUAKE_ANIMATION_RATE)
   schedule_quake(world, quake, ticks)
   return quake


def schedule_quake(world, quake, ticks):
   schedule_animation(world, quake, QUAKE_STEPS) 
   schedule_action(world, quake, world.create_entity_death_action(quake),
      ticks + QUAKE_DURATION)


def create_vein(world, name, pt, ticks, i_store):
   vein = entities.Vein("vein" + name,
      random.randint(VEIN_RATE_MIN, VEIN_RATE_MAX),
      pt, image_store.get_images(i_store, 'vein'))
   return vein


def schedule_vein(world, vein, ticks, i_store):
   schedule_action(world, vein, world.create_vein_action(vein, i_store),
      ticks + vein.get_rate())


def schedule_action(world, entity, action, time):
   entity.add_pending_action(action)
   world.schedule_action(action, time)


def schedule_animation(world, entity, repeat_count=0):
   schedule_action(world, entity,
      world.create_animation_action(entity, repeat_count),
      entity.get_animation_rate())


def clear_pending_actions(world, entity):
   for action in entity.get_pending_actions():
      world.unschedule_action(action)
   entity.clear_pending_actions()
