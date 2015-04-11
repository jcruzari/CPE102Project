import entities
import pygame
import ordered_list
import actions
import occ_grid
import point

BLOB_RATE_SCALE = 4
class WorldModel:
   def __init__(self, num_rows, num_cols, background):
      self.background = occ_grid.Grid(num_cols, num_rows, background)
      self.num_rows = num_rows
      self.num_cols = num_cols
      self.occupancy = occ_grid.Grid(num_cols, num_rows, None)
      self.entities = []
      self.action_queue = ordered_list.OrderedList()

   def within_bounds(self, pt):
      return (pt.x >= 0 and pt.x < self.num_cols and
         pt.y >= 0 and pt.y < self.num_rows)

   def is_occupied(self, pt):
      return (self.within_bounds(pt) and
         self.occupancy.get_cell(pt) != None)

   def find_nearest(self, pt, type):
      oftype = [(e, distance_sq(pt, e.get_position()))
         for e in self.entities if isinstance(e, type)]

      return nearest_entity(oftype)

   def add_entity(self, entity):
      pt = entity.get_position()
      if self.within_bounds(pt):
         old_entity = self.occupancy.get_cell(pt)
         if old_entity != None:
            entities.clear_pending_actions(old_entity)
         self.occupancy.set_cell(pt, entity)
         self.entities.append(entity)

   def move_entity(self, entity, pt):
      tiles = []
      if self.within_bounds(pt):
         old_pt = entity.get_position()
         self.occupancy.set_cell(old_pt, None)
         tiles.append(old_pt)
         self.occupancy.set_cell(pt, entity)
         tiles.append(pt)
         entity.set_position(pt)

      return tiles

   def remove_entity(self, entity):
      self.remove_entity_at(entity.get_position())

   def remove_entity_at(self, pt):
      if (self.within_bounds(pt) and
         self.occupancy.get_cell(pt) != None):
         entity = self.occupancy.get_cell(pt)
         entity.set_position(point.Point(-1, -1))
         self.entities.remove(entity)
         self.occupancy.set_cell(pt, None)

   def schedule_action(self, action, time):
      self.action_queue.insert(action, time)

   def unschedule_action(self, action):
      self.action_queue.remove(action)

   def update_on_time(self, ticks):
      tiles = []

      next = self.action_queue.head()
      while next and next.ord < ticks:
         self.action_queue.pop()
         tiles.extend(next.item(ticks))  # invoke action function
         next = self.action_queue.head()

      return tiles

   def get_background_image(self, pt):
      if self.within_bounds(pt):
        return entities.get_image(self.background.get_cell(pt))

   def get_background(self, pt):
      if self.within_bounds(pt):
         return self.background.get_cell(pt)

   def set_background(self, pt, bgnd):
      if self.within_bounds(pt):
         self.background.set_cell(pt, bgnd)

   def get_tile_occupant(self, pt):
      if self.within_bounds(pt):
         return self.occupancy.get_cell(pt)

   def get_entities(self):
      return self.entities

   #Possible methods from actions.py

   def next_position(self, entity_pt, dest_pt):
      horiz = actions.sign(dest_pt.x - entity_pt.x)
      new_pt = point.Point(entity_pt.x + horiz, entity_pt.y)

      if horiz == 0 or self.is_occupied(new_pt):
         vert = actions.sign(dest_pt.y - entity_pt.y)
         new_pt = point.Point(entity_pt.x, entity_pt.y + vert)

         if vert == 0 or self.is_occupied(new_pt):
            new_pt = point.Point(entity_pt.x, entity_pt.y)

      return new_pt

   def blob_next_position(self, entity_pt, dest_pt):
      horiz = actions.sign(dest_pt.x - entity_pt.x)
      new_pt = point.Point(entity_pt.x + horiz, entity_pt.y)

      if horiz == 0 or (self.is_occupied(new_pt) and
         not isinstance(self.get_tile_occupant(new_pt),
         entities.Ore)):
         vert = actions.sign(dest_pt.y - entity_pt.y)
         new_pt = point.Point(entity_pt.x, entity_pt.y + vert)

         if vert == 0 or (self.is_occupied(new_pt) and
            not isinstance(self.get_tile_occupant(new_pt),
            entities.Ore)):
            new_pt = point.Point(entity_pt.x, entity_pt.y)

      return new_pt

   def miner_to_ore(self, entity, ore):
      entity_pt = entity.get_position()
      if not ore:
         return ([entity_pt], False)
      ore_pt = ore.get_position()
      if actions.adjacent(entity_pt, ore_pt):
         entities.set_resource_count(entity,
            1 + entities.get_resource_count(entity))
         actions.remove_entity(self, ore)
         return ([ore_pt], True)
      else:
         new_pt = self.next_position(entity_pt, ore_pt)
         return (self.move_entity(entity, new_pt), False)

   def miner_to_smith(self, entity, smith):
      entity_pt = entity.get_position()
      if not smith:
         return ([entity_pt], False)
      smith_pt = smith.get_position()
      if actions.adjacent(entity_pt, smith_pt):
         entities.set_resource_count(smith,
            entities.get_resource_count(smith) +
            entities.get_resource_count(entity))
         entities.set_resource_count(entity, 0)
         return ([], True)
      else:
         new_pt = self.next_position(entity_pt, smith_pt)
         return (self.move_entity(entity, new_pt), False)

   def create_miner_not_full_action(self, entity, i_store):
      def action(current_ticks):
         entities.remove_pending_action(entity, action)

         entity_pt = entity.get_position()
         ore = self.find_nearest(entity_pt, entities.Ore)
         (tiles, found) = self.miner_to_ore(entity, ore)

         new_entity = entity
         if found:
            new_entity = self.try_transform_miner(entity,
               actions.try_transform_miner_not_full)

         actions.schedule_action(self, new_entity,
            self.create_miner_action(new_entity, i_store),
            current_ticks + new_entity.get_rate())
         return tiles
      return action

   def create_miner_full_action(self, entity, i_store):
      def action(current_ticks):
         entities.remove_pending_action(entity, action)

         entity_pt = entity.get_position()
         smith = self.find_nearest(entity_pt, entities.Blacksmith)
         (tiles, found) = self.miner_to_smith(entity, smith)

         new_entity = entity
         if found:
            new_entity = self.try_transform_miner(entity,
               actions.try_transform_miner_full)

         actions.schedule_action(self, new_entity,
            self.create_miner_action(new_entity, i_store),
            current_ticks + new_entity.get_rate())
         return tiles
      return action

   def blob_to_vein(self, entity, vein):
      entity_pt = entity.get_position()
      if not vein:
         return ([entity_pt], False)
      vein_pt = vein.get_position()
      if actions.adjacent(entity_pt, vein_pt):
         actions.remove_entity(self, vein)
         return ([vein_pt], True)
      else:
         new_pt = self.blob_next_position(entity_pt, vein_pt)
         old_entity = self.get_tile_occupant(new_pt)
         if isinstance(old_entity, entities.Ore):
            actions.remove_entity(self, old_entity)
         return (self.move_entity(entity, new_pt), False)

   def create_ore_blob_action(self, entity, i_store):
      def action(current_ticks):
         entities.remove_pending_action(entity, action)

         entity_pt = entity.get_position()
         vein = self.find_nearest(entity_pt, entities.Vein)
         (tiles, found) = self.blob_to_vein(entity, vein)

         next_time = current_ticks + entity.get_rate()
         if found:
            quake = actions.create_quake(self, tiles[0], current_ticks, i_store)
            self.add_entity(quake)
            next_time = current_ticks + entity.get_rate() * 2

         actions.schedule_action(self, entity,
            self.create_ore_blob_action(entity, i_store),
            next_time)

         return tiles
      return action

   def find_open_around(self, pt, distance):
      for dy in range(-distance, distance + 1):
         for dx in range(-distance, distance + 1):
            new_pt = point.Point(pt.x + dx, pt.y + dy)

            if (self.within_bounds(new_pt) and
               (not self.is_occupied(new_pt))):
               return new_pt

      return None

   def create_vein_action(self, entity, i_store):
      def action(current_ticks):
         entities.remove_pending_action(entity, action)

         open_pt = self.find_open_around(entity.get_position(),
            entity.get_resource_distance())
         if open_pt:
            ore = actions.create_ore(self,
               "ore - " + entity.get_name() + " - " + str(current_ticks),
               open_pt, current_ticks, i_store)
            self.add_entity(ore)
            tiles = [open_pt]
         else:
            tiles = []

         actions.schedule_action(self, entity,
            self.create_vein_action(entity, i_store),
            current_ticks + entity.get_rate())
         return tiles
      return action

   def try_transform_miner(self, entity, transform):
      new_entity = transform(self, entity)
      if entity != new_entity:
         actions.clear_pending_actions(self, entity)
         self.remove_entity_at(entity.get_position())
         self.add_entity(new_entity)
         actions.schedule_animation(self, new_entity)

      return new_entity

   def create_miner_action(self, entity, image_store):
      if isinstance(entity, entities.MinerNotFull):
         return self.create_miner_not_full_action(entity, image_store)
      else:
         return self.create_miner_full_action(entity, image_store)

   def create_animation_action(self, entity, repeat_count):
      def action(current_ticks):
         entities.remove_pending_action(entity, action)

         entities.next_image(entity)

         if repeat_count != 1:
            actions.schedule_action(self, entity,
               self.create_animation_action(entity, max(repeat_count - 1, 0)),
               current_ticks + entities.get_animation_rate(entity))

         return [entity.get_position()]
      return action

   def create_entity_death_action(self, entity):
      def action(current_ticks):
         entities.remove_pending_action(entity, action)
         pt = entity.get_position()
         actions.remove_entity(self, entity)
         return [pt]
      return action

   def create_ore_transform_action(self, entity, i_store):
      def action(current_ticks):
         entities.remove_pending_action(entity, action)
         blob = actions.create_blob(self, entity.get_name() + " -- blob",
            entity.get_position(),
            entity.get_rate() // BLOB_RATE_SCALE,
            current_ticks, i_store)

         actions.remove_entity(self, entity)
         self.add_entity(blob)

         return [blob.get_position()]
      return action

'''def within_bounds(world, pt):
   return (pt.x >= 0 and pt.x < world.num_cols and
      pt.y >= 0 and pt.y < world.num_rows)'''


'''def is_occupied(world, pt):
   return (world.within_bounds(pt) and
      occ_grid.get_cell(world.occupancy, pt) != None)'''


def nearest_entity(entity_dists):
   if len(entity_dists) > 0:
      pair = entity_dists[0]
      for other in entity_dists:
         if other[1] < pair[1]:
            pair = other
      nearest = pair[0]
   else:
      nearest = None

   return nearest


def distance_sq(p1, p2):
   return (p1.x - p2.x)**2 + (p1.y - p2.y)**2


'''def find_nearest(world, pt, type):
   oftype = [(e, distance_sq(pt, e.get_position()))
      for e in world.entities if isinstance(e, type)]

   return nearest_entity(oftype)'''


'''def add_entity(world, entity):
   pt = entity.get_position()
   if world.within_bounds(pt):
      old_entity = occ_grid.get_cell(world.occupancy, pt)
      if old_entity != None:
         entities.clear_pending_actions(old_entity)
      occ_grid.set_cell(world.occupancy, pt, entity)
      world.entities.append(entity)'''


'''def move_entity(world, entity, pt):
   tiles = []
   if world.within_bounds(pt):
      old_pt = entity.get_position()
      occ_grid.set_cell(world.occupancy, old_pt, None)
      tiles.append(old_pt)
      occ_grid.set_cell(world.occupancy, pt, entity)
      tiles.append(pt)
      entity.set_position(pt)

   return tiles'''


'''def remove_entity(world, entity):
   remove_entity_at(world, entity.get_position())'''


'''def remove_entity_at(world, pt):
   if (world.within_bounds(pt) and
      occ_grid.get_cell(world.occupancy, pt) != None):
      entity = occ_grid.get_cell(world.occupancy, pt)
      entity.set_position(point.Point(-1, -1))
      world.entities.remove(entity)
      occ_grid.set_cell(world.occupancy, pt, None)'''


'''def schedule_action(world, action, time):
   world.action_queue.insert(action, time)'''


'''def unschedule_action(world, action):
   world.action_queue.remove(action)'''


'''def update_on_time(world, ticks):
   tiles = []

   next = world.action_queue.head()
   while next and next.ord < ticks:
      world.action_queue.pop()
      tiles.extend(next.item(ticks))  # invoke action function
      next = world.action_queue.head()

   return tiles'''


'''def get_background_image(world, pt):
   if world.within_bounds(pt):
      return entities.get_image(occ_grid.get_cell(world.background, pt))'''


'''def get_background(world, pt):
   if world.within_bounds(pt):
      return occ_grid.get_cell(world.background, pt)'''


'''def set_background(world, pt, bgnd):
   if world.within_bounds(pt):
      occ_grid.set_cell(world.background, pt, bgnd)'''


'''def get_tile_occupant(world, pt):
   if world.within_bounds(pt):
      return occ_grid.get_cell(world.occupancy, pt)'''


'''def get_entities(world):
   return world.entities'''
