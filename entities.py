import point

class Entity(object):
   def __init__(self, name, position, rate, imgs):
      self.name = name
      self.position = position
      self.rate = rate
      self.imgs = imgs

   def set_position(self, point):
      self.position = point

   def get_position(self):
      return self.position

   def get_images(self):
      return self.imgs

   def get_rate(self):
      return self.rate

   def get_name(self):
      return self.name

   def get_animation_rate(self):
      return self.animation_rate

   def remove_pending_action(self, action):
      if hasattr(self, "pending_actions"):
         self.pending_actions.remove(action)

   def add_pending_action(self, action):
      if hasattr(self, "pending_actions"):
         self.pending_actions.append(action)


   def get_pending_actions(self):
      if hasattr(self, "pending_actions"):
         return self.pending_actions
      else:
         return []

   def clear_pending_actions(self):
      if hasattr(self, "pending_actions"):
         self.pending_actions = []

   def get_image(entity):
      return entity.imgs[entity.current_img]

   def set_resource_count(self, n):
      self.resource_count = n

   def get_resource_count(self):
      return self.resource_count

   def next_image(self):
      self.current_img = (self.current_img + 1) % len(self.imgs)

class Background(Entity):
   def __init__(self, name, imgs):
      self.name = name
      self.imgs = imgs
      self.current_img = 0

class Animated(Entity):
   def __init__(self, name, position, rate, imgs, animation_rate):
      self.animation_rate = animation_rate
      super(Animated, self).__init__(name, position, rate, imgs)

class Miner(Animated):
   def __init__(self, name, resource_limit, position, rate, imgs,
      animation_rate):
      super(Miner, self).__init__(name, position, rate, imgs, animation_rate)
      self.resource_limit = resource_limit

   def get_resource_limit(self):
      return self.resource_limit

class MinerNotFull(Miner):
   def __init__(self, name, resource_limit, position, rate, imgs,
      animation_rate):
      self.current_img = 0
      self.resource_count = 0
      self.pending_actions = []
      super(MinerNotFull, self).__init__(name, resource_limit, position, rate, imgs,
         animation_rate)

class MinerFull(Miner):
   def __init__(self, name, resource_limit, position, rate, imgs,
      animation_rate):
      self.current_img = 0
      self.resource_count = resource_limit
      self.pending_actions = []
      super(MinerFull, self).__init__(name, resource_limit, position, rate, imgs,
         animation_rate)

class Vein(Entity):
   def __init__(self, name, rate, position, imgs, resource_distance=1):
      super(Vein, self).__init__(name, position, rate, imgs)
      self.current_img = 0
      self.resource_distance = resource_distance
      self.pending_actions = []

   def get_resource_distance(self):
      return self.resource_distance

class Ore(Entity):
   def __init__(self, name, position, imgs, rate=5000):
      self.current_img = 0
      self.pending_actions = []
      super(Ore, self).__init__(name, position, rate, imgs)

class Blacksmith(Entity):
   def __init__(self, name, position, imgs, resource_limit, rate,
      resource_distance=1):
      self.current_img = 0
      self.resource_limit = resource_limit
      self.resource_count = 0
      self.resource_distance = resource_distance
      self.pending_actions = []
      super(Blacksmith, self).__init__(name, position, rate, imgs)

class Obstacle(Entity):
   def __init__(self, name, position, imgs):
      self.name = name
      self.position = position
      self.imgs = imgs
      self.current_img = 0

class OreBlob(Animated):
   def __init__(self, name, position, rate, imgs, animation_rate):
      super(OreBlob, self).__init__(name, position, rate, imgs, animation_rate)
      self.current_img = 0
      self.pending_actions = []

class Quake(Entity):
   def __init__(self, name, position, imgs, animation_rate):
      self.name = name
      self.position = position
      self.imgs = imgs
      self.current_img = 0
      self.animation_rate = animation_rate
      self.pending_actions = []

# This is a less than pleasant file format, but structured based on
# material covered in course.  Something like JSON would be a
# significant improvement.
def entity_string(entity):
   if isinstance(entity, MinerNotFull):
      return ' '.join(['miner', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.resource_limit),
         str(entity.rate), str(entity.animation_rate)])
   elif isinstance(entity, Vein):
      return ' '.join(['vein', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.rate),
         str(entity.resource_distance)])
   elif isinstance(entity, Ore):
      return ' '.join(['ore', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.rate)])
   elif isinstance(entity, Blacksmith):
      return ' '.join(['blacksmith', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.resource_limit),
         str(entity.rate), str(entity.resource_distance)])
   elif isinstance(entity, Obstacle):
      return ' '.join(['obstacle', entity.name, str(entity.position.x),
         str(entity.position.y)])
   else:
      return 'unknown'

