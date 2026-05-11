using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ContosoUniversity.Models
{
    public class Instructor : Person
    {
        [Required]
        [DataType(DataType.Date)]
        [DisplayFormat(DataFormatString = "{0:yyyy-MM-dd}", ApplyFormatInEditMode = true)]
        [Display(Name = "Hire Date")]
        [Column(TypeName = "datetime2")]
        [Range(typeof(DateTime), "1753-01-01", "9999-12-31", ErrorMessage = "Hire date must be between 1753 and 9999")]
        public DateTime HireDate { get; set; }

        public virtual ICollection<CourseAssignment> CourseAssignments { get; set; }
        public virtual OfficeAssignment OfficeAssignment { get; set; }
    }
}
