# Framework-Specific Parsers — codebase-functional-analyzer

Detailed parsing strategies for extracting routes, endpoints, middleware,
validation rules, and ORM models from each supported framework.

---

## Express / Node.js

### Route Extraction

```javascript
// Pattern 1: Direct app methods
app.get('/api/vehicles', authMiddleware, vehicleController.list);
app.post('/api/vehicles', authMiddleware, validate(schema), vehicleController.create);

// Pattern 2: Router instances
const router = express.Router();
router.get('/', list);
router.post('/', create);
router.get('/:id', getById);
app.use('/api/vehicles', router);

// Pattern 3: Route chaining
router.route('/vehicles')
  .get(list)
  .post(create);
```

**Extraction approach**:
1. Find all files importing `express` or `express.Router`
2. Track `app.use('/prefix', router)` to build full path prefixes
3. For each `app.METHOD()` or `router.METHOD()`:
   - Extract HTTP method (get/post/put/patch/delete)
   - Extract path (first string argument)
   - Extract handler function name (last argument)
   - Extract middleware (middle arguments)
4. Resolve handler references to find the actual function file/line

### Middleware Identification

Common Express middleware to tag:
| Middleware | Tag |
|---|---|
| `passport.authenticate()` | `auth_required: true` |
| `jwt()`, `verifyToken` | `auth_required: true` |
| `authorize('admin')`, `checkRole` | `auth_roles: [...]` |
| `validate()`, `celebrate()` | `has_validation: true` |
| `rateLimit()` | `rate_limited: true` |
| `cors()` | `cors_enabled: true` |
| `multer()`, `upload` | `file_upload: true` |

### Validation (express-validator / Joi)

```javascript
// express-validator
body('name').notEmpty().isLength({ max: 100 }),
body('email').isEmail().normalizeEmail(),
body('type').isIn(['Heavy', 'Light', 'Medium']),

// Joi
Joi.object({
  name: Joi.string().required().max(100),
  email: Joi.string().email().required(),
  type: Joi.string().valid('Heavy', 'Light', 'Medium').required()
})
```

**Map to field validations**:
- `.notEmpty()` / `.required()` → `required: true`
- `.isLength({ max: N })` / `.max(N)` → `max_length: N`
- `.isEmail()` / `.email()` → `type: "email"`
- `.isIn([...])` / `.valid(...)` → `type: "enum", values: [...]`
- `.matches(regex)` / `.pattern(regex)` → `validation_regex: "..."`

---

## Next.js

### API Route Extraction

**Pages Router** (`pages/api/`):
```
pages/api/vehicles/index.ts    → GET/POST /api/vehicles
pages/api/vehicles/[id].ts     → GET/PUT/DELETE /api/vehicles/:id
pages/api/auth/[...nextauth].ts → /api/auth/*
```

Parse exported functions: `export default handler` or named exports
`export { GET, POST }` (App Router).

**App Router** (`app/`):
```
app/api/vehicles/route.ts      → GET/POST /api/vehicles
app/api/vehicles/[id]/route.ts  → GET/PUT/DELETE /api/vehicles/:id
```

Parse named exports: `export async function GET()`, `POST()`, `PUT()`, `DELETE()`.

### Frontend Route Discovery

**Pages Router**: Each file in `pages/` = a route:
```
pages/index.tsx          → /
pages/dashboard.tsx      → /dashboard
pages/vehicles/index.tsx → /vehicles
pages/vehicles/[id].tsx  → /vehicles/:id
```

**App Router**: Each `page.tsx` in `app/`:
```
app/page.tsx              → /
app/dashboard/page.tsx    → /dashboard
app/(admin)/users/page.tsx → /users (route group)
app/vehicles/[id]/page.tsx → /vehicles/:id
```

### Middleware

Check `middleware.ts` at project root — Next.js middleware runs on all
matching routes:
```typescript
export function middleware(request: NextRequest) { ... }
export const config = { matcher: ['/dashboard/:path*', '/api/:path*'] };
```

---

## Django

### URL Pattern Extraction

```python
# urls.py
urlpatterns = [
    path('api/vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('api/vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('api/vehicles/<int:pk>/bookings/', VehicleBookingsView.as_view()),
]
```

**DRF ViewSets with Router**:
```python
router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)
# Auto-generates: GET/POST /vehicles/, GET/PUT/PATCH/DELETE /vehicles/{pk}/
```

### Model Extraction

```python
class Vehicle(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    plate_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, default='Active')
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE, related_name='vehicles')
    created_at = models.DateTimeField(auto_now_add=True)
```

**Map to model fields**:
- `CharField(max_length=N)` → `type: "string", max_length: N`
- `IntegerField()` → `type: "integer"`
- `choices=CHOICES` → `type: "enum", values: [...]`
- `unique=True` → `unique: true`
- `ForeignKey(Model)` → `relationships: [{type: "belongsTo", target: "Model"}]`
- `auto_now_add=True` → `auto_generated: true`

### DRF Serializer Validation

```python
class VehicleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, required=True)
    plate_number = serializers.RegexField(regex=r'^[A-Z]{2}[0-9]{4}$')
```

---

## Spring Boot

### Controller Extraction

```java
@RestController
@RequestMapping("/api/vehicles")
public class VehicleController {

    @GetMapping
    public List<Vehicle> list() { ... }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public Vehicle create(@Valid @RequestBody CreateVehicleRequest request) { ... }

    @GetMapping("/{id}")
    public Vehicle getById(@PathVariable Long id) { ... }

    @PutMapping("/{id}")
    public Vehicle update(@PathVariable Long id, @Valid @RequestBody UpdateVehicleRequest request) { ... }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) { ... }
}
```

**Extraction**:
- `@RequestMapping` on class → base path prefix
- `@GetMapping`, `@PostMapping`, etc. → HTTP method + path
- `@Valid @RequestBody` → request body with validation
- `@PreAuthorize` → auth roles
- `@PathVariable` → path parameters
- `@RequestParam` → query parameters

### Bean Validation

```java
public class CreateVehicleRequest {
    @NotBlank
    @Size(max = 100)
    private String name;

    @NotNull
    private VehicleType type;

    @NotBlank
    @Pattern(regexp = "^[A-Z]{2}[0-9]{4}$")
    private String plateNumber;
}
```

**Map**:
- `@NotBlank` / `@NotNull` → `required: true`
- `@Size(max = N)` → `max_length: N`
- `@Pattern(regexp = "...")` → `validation_regex: "..."`
- `@Email` → `type: "email"`
- `@Min(N)` / `@Max(N)` → `boundary_min/max`

### JPA Entity Extraction

```java
@Entity
@Table(name = "vehicles")
public class Vehicle {
    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 100)
    private String name;

    @Enumerated(EnumType.STRING)
    private VehicleType type;

    @Column(unique = true)
    private String plateNumber;

    @ManyToOne
    @JoinColumn(name = "fleet_id")
    private Fleet fleet;

    @OneToMany(mappedBy = "vehicle")
    private List<Booking> bookings;
}
```

---

## FastAPI

### Route Extraction

```python
@app.get("/api/vehicles", response_model=list[VehicleOut])
async def list_vehicles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    ...

@app.post("/api/vehicles", response_model=VehicleOut, status_code=201)
async def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    ...
```

### Pydantic Model Validation

```python
class VehicleCreate(BaseModel):
    name: str = Field(..., max_length=100)
    type: VehicleType  # Enum
    plate_number: str = Field(..., regex=r'^[A-Z]{2}[0-9]{4}$')

    class Config:
        schema_extra = {"example": {"name": "Truck A", "type": "Heavy"}}
```

**Map**:
- `str = Field(...)` → `required: true, type: "string"`
- `Field(max_length=N)` → `max_length: N`
- `Field(regex=...)` → `validation_regex`
- `Optional[str]` → `required: false`
- Enum type → `type: "enum", values: [...]`

---

## Laravel

### Route Extraction

```php
// routes/api.php
Route::middleware(['auth:sanctum'])->group(function () {
    Route::apiResource('vehicles', VehicleController::class);
    Route::get('vehicles/{vehicle}/bookings', [VehicleController::class, 'bookings']);
});
```

`Route::apiResource` auto-generates: index, store, show, update, destroy.

### Form Request Validation

```php
class StoreVehicleRequest extends FormRequest {
    public function rules(): array {
        return [
            'name' => 'required|string|max:100',
            'type' => 'required|in:Heavy,Light,Medium',
            'plate_number' => 'required|string|unique:vehicles|regex:/^[A-Z]{2}[0-9]{4}$/',
        ];
    }
}
```

### Eloquent Model

```php
class Vehicle extends Model {
    protected $fillable = ['name', 'type', 'plate_number', 'status'];
    protected $casts = ['type' => VehicleType::class];

    public function fleet() { return $this->belongsTo(Fleet::class); }
    public function bookings() { return $this->hasMany(Booking::class); }
}
```

---

## Rails

### Route Extraction

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    resources :vehicles do
      resources :bookings, only: [:index, :create]
    end
  end
end
```

`resources :vehicles` generates all 7 RESTful routes.

### ActiveModel Validation

```ruby
class Vehicle < ApplicationRecord
  validates :name, presence: true, length: { maximum: 100 }
  validates :type, presence: true, inclusion: { in: %w[Heavy Light Medium] }
  validates :plate_number, presence: true, uniqueness: true,
            format: { with: /\A[A-Z]{2}[0-9]{4}\z/ }

  belongs_to :fleet
  has_many :bookings
end
```

---

## ASP.NET

### Controller Extraction

```csharp
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class VehiclesController : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<IEnumerable<Vehicle>>> GetAll() { ... }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<Vehicle>> Create([FromBody] CreateVehicleDto dto) { ... }

    [HttpGet("{id}")]
    public async Task<ActionResult<Vehicle>> GetById(int id) { ... }
}
```

### Data Annotations

```csharp
public class CreateVehicleDto
{
    [Required]
    [StringLength(100)]
    public string Name { get; set; }

    [Required]
    public VehicleType Type { get; set; }

    [Required]
    [RegularExpression(@"^[A-Z]{2}[0-9]{4}$")]
    public string PlateNumber { get; set; }
}
```

### Entity Framework

```csharp
public class Vehicle
{
    public int Id { get; set; }
    public string Name { get; set; }
    public VehicleType Type { get; set; }
    public string PlateNumber { get; set; }

    public int FleetId { get; set; }
    public Fleet Fleet { get; set; }
    public ICollection<Booking> Bookings { get; set; }
}
```
