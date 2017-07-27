using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public abstract class WorldObject : MonoBehaviour
{
    public WorldScript.Kind kind;

    public abstract void UpdateWorldObject(float[] data);

    static public Vector3 GetVec3(float[] data, int index)
    {
        return new Vector3(data[index], data[index + 2], data[index + 1]);
    }

    static public Color GetColor24(float[] data, int index)
    {
        /* Note: only for alpha-less colors.  A float holds only 24 bits of precision */
        uint color = (uint)data[index];
        return new Color(((color >> 16) & 0xff) / 255f,
                         ((color >> 8) & 0xff) / 255f,
                         (color & 0xff) / 255f);
    }

    static public string GetString(float[] data, ref int index)
    {
        var sb = new System.Text.StringBuilder();
        int text_length = (int)data[index++];
        for (int i = 1; i <= text_length; i++)
            sb.Append((char)data[index++]);
        return sb.ToString();
    }


    public class MaterialCache
    {
        public delegate void BuildDelegate(Material mat, Color col);

        Material base_material;
        Dictionary<Color, Material> cache;
        BuildDelegate build_delegate;

        public MaterialCache(Material base_material, BuildDelegate build = null)
        {
            this.base_material = base_material;
            cache = new Dictionary<Color, Material>();
            if (build == null)
                cache[base_material.color] = base_material;
            build_delegate = build != null ? build : BuildDefaultMaterial;
        }

        static void BuildDefaultMaterial(Material mat, Color col)
        {
            mat.color = col;
        }

        public Material Get(Color col)
        {
            Material mat;
            if (!cache.TryGetValue(col, out mat))
            {
                mat = new Material(base_material);
                build_delegate(mat, col);
                cache[col] = mat;
            }
            return mat;
        }

        public Material Get()
        {
            return base_material;
        }
    }
}
