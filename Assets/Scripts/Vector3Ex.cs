using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;


namespace VRSketch3
{
#if false
    /* Linear and affine subspaces of the 3D space 
     */

    public struct PointedSubspace
    {
        public Subspace subspace;
        public Vector3 point0;

        public PointedSubspace(Subspace subspace, Vector3 point0)
        {
            this.subspace = subspace;
            this.point0 = point0;
        }

        public bool IsEmpty()
        {
            return (Mathf.Abs(point0.x) == Mathf.Infinity ||
                    Mathf.Abs(point0.y) == Mathf.Infinity ||
                    Mathf.Abs(point0.z) == Mathf.Infinity);
        }

        public Vector3 Snap(Vector3 point)
        {
            if (IsEmpty())
                return point;
            return subspace.Project(point - point0) + point0;
        }

        public float Distance(Vector3 point)
        {
            if (IsEmpty())
                return float.PositiveInfinity;
            return Vector3.Distance(point, Snap(point));
        }

        public PointedSubspace IntersectedWith(PointedSubspace other)
        {
            if (IsEmpty())
                return this;
            if (other.IsEmpty())
                return other;

            var res = subspace.IntersectedWith(new PointedSubspace(other.subspace, other.point0 - point0));
            return new PointedSubspace(res.subspace, res.point0 + point0);
        }

        public static PointedSubspace Void()
        {
            return new PointedSubspace(new Subspace0(), VEC3_INFINITY);
        }

        static readonly Vector3 VEC3_INFINITY = new Vector3(
            float.PositiveInfinity, float.PositiveInfinity, float.PositiveInfinity);
    }


    public abstract class Subspace
    {
        public abstract Subspace JoinedWithVector(Vector3 v);
        public abstract Subspace NormalSubspace();
        public abstract Vector3 Project(Vector3 v);
        public abstract Subspace IntersectedWith(Subspace other);
        public abstract PointedSubspace IntersectedWith(PointedSubspace other);

        public Subspace IntersectedWithPlane(Vector3 normal)
        {
            return NormalSubspace().JoinedWithVector(normal).NormalSubspace();
        }

        public Subspace IntersectedWithSingleVector(Vector3 v)
        {
            v = Project(v);
            return new Subspace0().JoinedWithVector(v);
        }

        protected Vector3? _intersect_plane_line(Vector3 normal, Vector3 plane_pt, Vector3 line_origin, Vector3 line_direction)
        {
            /* XXX can be much optimized */
            normal.Normalize();
            line_direction.Normalize();

            Plane plane = new Plane(normal, plane_pt);
            float enter;
            if (plane.Raycast(new Ray(line_origin, line_direction), out enter))
                return line_origin + line_direction * enter;
            if (plane.Raycast(new Ray(Vector3.zero, -line_direction), out enter))
                return line_origin - line_direction * enter;
            return null;
        }
    }

    public class Subspace0 : Subspace
    {
        public Subspace0() { }

        public override Subspace JoinedWithVector(Vector3 v)
        {
            if (v == Vector3.zero)
                return this;
            return new Subspace1(v);
        }

        public override Subspace NormalSubspace()
        {
            return new Subspace3();
        }

        public override Vector3 Project(Vector3 v)
        {
            return Vector3.zero;
        }

        public override Subspace IntersectedWith(Subspace other)
        {
            return this;
        }

        public override PointedSubspace IntersectedWith(PointedSubspace other)
        {
            if (other.Snap(Vector3.zero) == Vector3.zero)
                return new PointedSubspace(this, Vector3.zero);
            else
                return PointedSubspace.Void();
        }
    }

    public class Subspace1 : Subspace
    {
        public readonly Vector3 axis;

        public Subspace1(Vector3 axis) { this.axis = axis; }

        public override Subspace JoinedWithVector(Vector3 v)
        {
            Vector3 normal = Vector3.Cross(axis, v);
            if (normal == Vector3.zero)
                return this;
            return new Subspace2(normal);
        }

        public override Subspace NormalSubspace()
        {
            return new Subspace2(axis);
        }

        public override Vector3 Project(Vector3 v)
        {
            return Vector3.Project(v, axis);
        }

        public override Subspace IntersectedWith(Subspace other)
        {
            if (other.Project(axis) == axis)
                return this;
            return new Subspace0();
        }

        public override PointedSubspace IntersectedWith(PointedSubspace other)
        {
            if (other.Snap(Vector3.zero) == Vector3.zero)
                return new PointedSubspace(IntersectedWith(other.subspace), Vector3.zero);

            if (other.subspace is Subspace2)
            {
                Vector3? intersect = _intersect_plane_line(
                    ((Subspace2)other.subspace).normal, other.point0,
                    Vector3.zero, axis);
                if (intersect.HasValue)
                    return new PointedSubspace(new Subspace0(), intersect.Value);
            }
            /* XXX missing special case if other.subspace is a specially aligned Subspace1 */
            return PointedSubspace.Void();
        }
    }

    public class Subspace2 : Subspace
    {
        public readonly Vector3 normal;

        public Subspace2(Vector3 normal) { this.normal = normal; }

        public override Subspace JoinedWithVector(Vector3 v)
        {
            if (Vector3.Dot(v, normal) == 0)
                return this;
            return new Subspace3();
        }

        public override Subspace NormalSubspace()
        {
            return new Subspace1(normal);
        }

        public override Vector3 Project(Vector3 v)
        {
            return Vector3.ProjectOnPlane(v, normal);
        }

        public override Subspace IntersectedWith(Subspace other)
        {
            return other.NormalSubspace().JoinedWithVector(normal).NormalSubspace();
        }

        public override PointedSubspace IntersectedWith(PointedSubspace other)
        {
            if (other.Snap(Vector3.zero) == Vector3.zero)
                return new PointedSubspace(IntersectedWith(other.subspace), Vector3.zero);

            if (other.subspace is Subspace1)
            {
                Vector3? intersect = _intersect_plane_line(
                    normal, Vector3.zero,
                    other.point0, ((Subspace1)other.subspace).axis);
                if (intersect.HasValue)
                    return new PointedSubspace(new Subspace0(), intersect.Value);
            }
            else if (other.subspace is Subspace2)
            {
                Subspace ss = other.subspace.NormalSubspace().JoinedWithVector(normal);
                if (ss is Subspace2)
                {
                    Vector3 intersect_normal = ((Subspace2)ss).normal;
                    Subspace ss2 = IntersectedWithPlane(intersect_normal);   /* a Subspace1 */
                    PointedSubspace pss2 = ss2.IntersectedWith(other);
                    return new PointedSubspace(ss.NormalSubspace(), pss2.point0);
                }
            }
            return PointedSubspace.Void();
        }
    }

    public class Subspace3 : Subspace
    {
        public Subspace3() { }

        public override Subspace JoinedWithVector(Vector3 v)
        {
            return this;
        }

        public override Subspace NormalSubspace()
        {
            return new Subspace0();
        }

        public override Vector3 Project(Vector3 v)
        {
            return v;
        }

        public override Subspace IntersectedWith(Subspace other)
        {
            return other;
        }

        public override PointedSubspace IntersectedWith(PointedSubspace other)
        {
            return other;
        }
    }
#endif


    public static class PlaneRecomputer
    {
        public static Plane RecomputePlane(Vector3[] vertices)
        {
            Vector3 center = Vector3.zero;
            foreach (var v in vertices)
                center += v;
            center /= vertices.Length;

            var A = new DotNetMatrix.GeneralMatrix(3, 3);
            double[] r = new double[3];

            foreach (var v in vertices)
            {
                Vector3 p = v - center;
                r[0] = p.x;
                r[1] = p.y;
                r[2] = p.z;
                for (int j = 0; j < 3; j++)
                    for (int i = j; i < 3; i++)
                        A.Array[j][i] += r[i] * r[j];
            }
            for (int j = 1; j < 3; j++)
                for (int i = 0; i < j; i++)
                    A.Array[j][i] = A.Array[i][j];

            var E = A.Eigen();
            var minimal_eigenvalue = E.RealEigenvalues[0];
            int pick = 0;
            for (int i = 1; i < 3; i++)
            {
                if (E.RealEigenvalues[i] < minimal_eigenvalue)
                {
                    minimal_eigenvalue = E.RealEigenvalues[i];
                    pick = i;
                }
            }
            var eigenvectors = E.GetV();
            var normal = new Vector3((float)eigenvectors.Array[0][pick],
                                     (float)eigenvectors.Array[1][pick],
                                     (float)eigenvectors.Array[2][pick]);
            return new Plane(normal, center);
        }
    }
}
