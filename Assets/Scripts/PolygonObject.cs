using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using VRSketch3;


public class PolygonObject : WorldObject
{
    public override void UpdateWorldObject(float[] data)
    {
        var vertices = new Vector3[data.Length / 3];
        for (int i = 0; i < vertices.Length; i++)
            vertices[i] = GetVec3(data, i * 3);

        ComputeMesh(vertices);

        if (kind == WorldScript.Kind.ColoredPolygon)
        {
            Color col = GetColor24(data, vertices.Length * 3);
            GetComponent<MeshRenderer>().material.color = col;
        }
        else if (kind == WorldScript.Kind.PolygonHighlight)
        {
            Color col = GetColor24(data, vertices.Length * 3);
            Material mat = GetComponent<MeshRenderer>().material;
            mat.SetColor("g_vOutlineColor", col);
            mat.SetColor("g_vMaskedOutlineColor", Color.Lerp(Color.black, col, 0.7f));
        }
    }

    void ComputeMesh(Vector3[] vertices)
    {
        Plane plane = PlaneRecomputer.RecomputePlane(vertices);

        var vpositions = new List<Vector3>();
        var vnormals = new List<Vector3>();
        var triangles = new List<int>();

        /* add vertices and normals to the lists, twice, for the opposite normals */
        int face_vstart = vpositions.Count;
        foreach (var vertex in vertices)
        {
            vpositions.Add(vertex);
            vnormals.Add(plane.normal);
        }

        int face_vstart_back = vpositions.Count;
        foreach (var vertex in vertices)
        {
            vpositions.Add(vertex);
            vnormals.Add(-plane.normal);
        }

        /* cast the vertexes on the 2D plane, so we can compute triangulation. */
        var uvs = ProjectOnPlane(plane, vertices);
        var triangulator = new Triangulator(uvs);
        var triangulation = triangulator.Triangulate();

        /* 'triangles' are given two copies of triangulation going different way
            and having different vertexes */
        for (var i = 0; i < triangulation.Length / 3; ++i)
        {
            triangles.Add(face_vstart + triangulation[3 * i]);
            triangles.Add(face_vstart + triangulation[3 * i + 2]);
            triangles.Add(face_vstart + triangulation[3 * i + 1]);
            triangles.Add(face_vstart_back + triangulation[3 * i + 1]);
            triangles.Add(face_vstart_back + triangulation[3 * i + 2]);
            triangles.Add(face_vstart_back + triangulation[3 * i]);
        }

        /* build the mesh */
        var mesh = new Mesh();
        mesh.vertices = vpositions.ToArray();
        mesh.normals = vnormals.ToArray();
        mesh.triangles = triangles.ToArray();
        mesh.RecalculateBounds();

        GetComponent<MeshFilter>().sharedMesh = mesh;
    }

    static Vector2[] ProjectOnPlane(Plane plane, Vector3[] vertices)
    {
        Vector3 plane1, plane2;
        Vector3 normal = plane.normal;
        if (Mathf.Abs(normal.y) < Mathf.Max(normal.x, normal.z))
            plane1 = new Vector3(0, 1, 0);
        else
            plane1 = new Vector3(1, 0, 0);

        plane1 = Vector3.ProjectOnPlane(plane1, normal).normalized;
        plane2 = Vector3.Cross(normal, plane1);

        var uvs = new Vector2[vertices.Length];
        for (int i = 0; i < uvs.Length; i++)
        {
            Vector3 point = vertices[i];
            uvs[i] = new Vector2(Vector3.Dot(point, plane1), Vector3.Dot(point, plane2));
        }
        return uvs;
    }
}
